using System.Diagnostics;

namespace Altin_Fiyat_Takip_Analizi.API.BackgroundServices;

/// <summary>
/// API process'i ayakta olduğu sürece her 1 dakikada bir
/// scraper/sync_own_prices.py script'ini çalıştırıp kendi mağaza fiyatlarını günceller.
/// Scheduler projesinden bağımsızdır — API ile birlikte her zaman aktiftir.
/// </summary>
public class OwnPriceSyncBackgroundService : BackgroundService
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<OwnPriceSyncBackgroundService> _logger;

    // Her 1 dakikada bir çalış
    private static readonly TimeSpan Interval = TimeSpan.FromMinutes(1);

    public OwnPriceSyncBackgroundService(
        IConfiguration configuration,
        ILogger<OwnPriceSyncBackgroundService> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation(
            "OwnPriceSyncBackgroundService başlatıldı — her {Minutes} dakikada bir çalışacak.",
            Interval.TotalMinutes);

        // İlk çalışmayı hemen yap (başlangıç gecikmesi olmadan)
        await RunSyncAsync(stoppingToken);

        // Sonrakiler 5 dakika bekleyerek
        using var timer = new PeriodicTimer(Interval);
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await timer.WaitForNextTickAsync(stoppingToken);
            }
            catch (OperationCanceledException)
            {
                break; // Host kapanıyor
            }

            await RunSyncAsync(stoppingToken);
        }

        _logger.LogInformation("OwnPriceSyncBackgroundService durduruldu.");
    }

    private async Task RunSyncAsync(CancellationToken stoppingToken)
    {
        var pythonPath = _configuration["Scraper:PythonPath"] ?? "python";
        var workingDirectory = _configuration["Scraper:WorkingDirectory"];

        if (string.IsNullOrWhiteSpace(workingDirectory))
        {
            _logger.LogWarning(
                "OwnPriceSync atlandı: Scraper:WorkingDirectory appsettings.json'da tanımlı değil.");
            return;
        }

        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = "-m scraper.sync_own_prices",
                WorkingDirectory = workingDirectory,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            _logger.LogInformation(
                "OwnPriceSync başlatılıyor: {Python} -m scraper.sync_own_prices",
                pythonPath);

            using var process = Process.Start(psi)
                ?? throw new InvalidOperationException("sync_own_prices process başlatılamadı.");

            // Deadlock'ı önlemek için stream'leri WaitForExit'ten ÖNCE başlat
            var outputTask = process.StandardOutput.ReadToEndAsync(stoppingToken);
            var errorTask  = process.StandardError.ReadToEndAsync(stoppingToken);

            var timeoutSeconds = _configuration.GetValue<int>("Scraper:OwnPriceSyncTimeoutSeconds", 300);
            var completed = process.WaitForExit(timeoutSeconds * 1000);

            var output = await outputTask;
            var error  = await errorTask;

            if (!completed)
            {
                process.Kill();
                _logger.LogError(
                    "OwnPriceSync zaman aşımına uğradı ({Timeout}s). stderr: {Error}",
                    timeoutSeconds, error);
                return;
            }

            if (process.ExitCode != 0)
            {
                _logger.LogError(
                    "OwnPriceSync hata ile sonlandı (kod {ExitCode}). stderr: {Error}",
                    process.ExitCode, error);
                return;
            }

            _logger.LogInformation("OwnPriceSync tamamlandı. Çıktı: {Output}", output);
        }
        catch (OperationCanceledException)
        {
            _logger.LogInformation("OwnPriceSync host kapanışı nedeniyle iptal edildi.");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "OwnPriceSyncBackgroundService çalıştırılırken beklenmeyen hata oluştu.");
        }
    }
}
