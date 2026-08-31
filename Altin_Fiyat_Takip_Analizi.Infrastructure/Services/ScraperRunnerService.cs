using System.Collections.Concurrent;
using System.Diagnostics;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Infrastructure.Data;

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Services;

public class ScraperRunnerService : IScraperRunnerService
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<ScraperRunnerService> _logger;
    private readonly IServiceScopeFactory _scopeFactory;

    // Platform bazında eşzamanlı tek işlem kilidi
    private readonly ConcurrentDictionary<string, SemaphoreSlim> _locks = new(StringComparer.OrdinalIgnoreCase);

    // Son tarama zamanları (in-memory)
    private readonly ConcurrentDictionary<string, DateTime> _lastScrapedAt = new(StringComparer.OrdinalIgnoreCase);

    // Aktif çalışan işlemler
    private readonly ConcurrentDictionary<string, bool> _activeScrapes = new(StringComparer.OrdinalIgnoreCase);

    // Aynı platform için minimum tarama aralığı (throttle)
    private static readonly TimeSpan ThrottleInterval = TimeSpan.FromMinutes(1);

    public ScraperRunnerService(
        IConfiguration configuration, 
        ILogger<ScraperRunnerService> logger,
        IServiceScopeFactory scopeFactory)
    {
        _configuration = configuration;
        _logger = logger;
        _scopeFactory = scopeFactory;
    }

    public bool IsScraping(string platform)
    {
        var key = NormalizeKey(platform);
        return _activeScrapes.TryGetValue(key, out var active) && active;
    }

    public DateTime? GetLastScrapedAt(string platform)
    {
        var key = NormalizeKey(platform);
        DateTime? memoryDt = _lastScrapedAt.TryGetValue(key, out var dt) ? dt : null;

        try
        {
            using var scope = _scopeFactory.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();

            string urlFilter = key switch
            {
                "n11" => "%n11.com%",
                "pttavm" => "%pttavm.com%",
                "pazarama" => "%pazarama.com%",
                _ => $"%{key}%"
            };

            var dbDt = db.PriceHistories
                .AsNoTracking()
                .Where(p => EF.Functions.Like(p.SellerProduct.ExternalUrl, urlFilter))
                .OrderByDescending(p => p.Id)
                .Select(p => (DateTime?)p.CollectedAt)
                .FirstOrDefault();

            if (dbDt.HasValue)
            {
                if (!memoryDt.HasValue || dbDt.Value > memoryDt.Value)
                    return dbDt.Value;
            }
        }
        catch
        {
            // DB sorgusunda hata olursa bellektekini dön
        }

        return memoryDt;
    }

    public async Task<bool> TriggerScrapeAsync(string platform, bool force = false, bool waitForRunning = false)
    {
        var key = NormalizeKey(platform);
        var sem = _locks.GetOrAdd(key, _ => new SemaphoreSlim(1, 1));

        // Eğer şu anda bu platform taranıyorsa:
        if (!await sem.WaitAsync(0))
        {
            if (waitForRunning)
            {
                _logger.LogInformation("Scraper [{Platform}] şu anda zaten çalışıyor. Bitmesi bekleniyor...", key);
                // Çalışan taramanın bitmesini bekle
                var acquired = await sem.WaitAsync(TimeSpan.FromMinutes(2.5));
                if (acquired)
                {
                    try
                    {
                        _logger.LogInformation("Scraper [{Platform}] önceki taraması az önce tamamlandı, veriler güncel.", key);
                        return true;
                    }
                    finally
                    {
                        sem.Release();
                    }
                }
            }

            _logger.LogInformation("Scraper [{Platform}] zaten şu anda çalışıyor, yeni istek atlandı.", key);
            return false;
        }

        try
        {
            // Throttle kontrolü: Son 1 dakika içinde taranmışsa ve force değilse atla
            if (!force && _lastScrapedAt.TryGetValue(key, out var lastTime))
            {
                var elapsed = DateTime.UtcNow - lastTime;
                if (elapsed < ThrottleInterval)
                {
                    _logger.LogInformation(
                        "Scraper [{Platform}] yakın zamanda ({Seconds:N0} sn önce) tarandı, throttle nedeniyle atlandı.",
                        key, elapsed.TotalSeconds);
                    return true; // Zaten güncel
                }
            }

            _activeScrapes[key] = true;

            var pythonPath = _configuration["Scraper:PythonPath"] ?? "python";
            var workingDirectory = _configuration["Scraper:WorkingDirectory"];

            if (string.IsNullOrWhiteSpace(workingDirectory))
            {
                _logger.LogWarning("Scraper:WorkingDirectory appsettings.json'da tanımlı değil.");
                return false;
            }

            // Platforma göre Python argümanlarını belirle
            var arguments = ResolveArguments(key);

            _logger.LogInformation("Canlı Scraper başlatılıyor: {Python} {Args} (Dizin: {Dir})",
                pythonPath, arguments, workingDirectory);

            var psi = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = arguments,
                WorkingDirectory = workingDirectory,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null)
            {
                _logger.LogError("Scraper process başlatılamadı: {Platform}", key);
                return false;
            }

            // Pipe buffer dolup deadlock oluşmaması için stdout ve stderr'i asenkron oku
            var stdoutTask = process.StandardOutput.ReadToEndAsync();
            var stderrTask = process.StandardError.ReadToEndAsync();

            using var cts = new CancellationTokenSource(TimeSpan.FromMinutes(3));
            await process.WaitForExitAsync(cts.Token);

            var stdout = await stdoutTask;
            var stderr = await stderrTask;

            _lastScrapedAt[key] = DateTime.UtcNow;
            _logger.LogInformation("Scraper [{Platform}] tamamlandı (ExitCode: {Code}).", key, process.ExitCode);

            if (process.ExitCode != 0)
            {
                _logger.LogWarning("Scraper [{Platform}] hata çıktısı: {Stderr}", key, stderr);
            }

            return process.ExitCode == 0;
        }
        catch (OperationCanceledException)
        {
            _logger.LogWarning("Scraper [{Platform}] zaman aşımına uğradı (3 dk limit).", key);
            return false;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Scraper [{Platform}] çalışırken hata oluştu.", key);
            return false;
        }
        finally
        {
            _activeScrapes[key] = false;
            sem.Release();
        }
    }

    private static string NormalizeKey(string platform)
    {
        if (string.IsNullOrWhiteSpace(platform)) return "all";
        return platform.Trim().ToLowerInvariant();
    }

    private static string ResolveArguments(string platform)
    {
        return platform switch
        {
            "pazarama" => "-m scraper.main --seller pazarama",
            "pttavm" => "-m scraper.main --seller pttavm",
            "n11" => "-m scraper.main --seller n11",
            "own" => "-m scraper.sync_own_prices",
            _ => "-m scraper.main"
        };
    }
}
