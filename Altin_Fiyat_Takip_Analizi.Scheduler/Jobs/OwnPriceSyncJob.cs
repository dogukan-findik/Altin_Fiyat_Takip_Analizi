using System.Diagnostics;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.IO;
using Quartz;

namespace Altin_Fiyat_Takip_Analizi.Scheduler.Jobs;

/// <summary>
/// Ahlatcı Store kendi mağaza fiyatlarını (sync_own_prices.py) her 5 dakikada bir günceller.
/// Bu job PriceCollectionJob'dan bağımsızdır — kendi ayrı zamanlayıcısı vardır.
/// </summary>
public class OwnPriceSyncJob : IJob
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<OwnPriceSyncJob> _logger;

    public OwnPriceSyncJob(IConfiguration configuration, ILogger<OwnPriceSyncJob> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    public async Task Execute(IJobExecutionContext context)
    {
        var pythonPath = _configuration["Scraper:PythonPath"] ?? "python";
        var workingDirectory = _configuration["Scraper:WorkingDirectory"]
            ?? throw new InvalidOperationException("Scraper:WorkingDirectory appsettings.json'da tanımlı değil.");

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
                "OwnPriceSync başlatılıyor: {Python} -m scraper.sync_own_prices (WorkingDirectory: {Dir})",
                pythonPath, workingDirectory);

            using var process = Process.Start(psi)
                ?? throw new InvalidOperationException("sync_own_prices process başlatılamadı.");

            // Okuma işlemlerini await veya Task ile başlatıp Deadlock olmasını önlüyoruz!
            var outputTask = process.StandardOutput.ReadToEndAsync();
            var errorTask = process.StandardError.ReadToEndAsync();

            var timeoutMs = int.Parse(_configuration["Scraper:OwnPriceSyncTimeoutSeconds"] ?? "300") * 1000;
            var completed = process.WaitForExit(timeoutMs);

            var output = await outputTask;
            var error = await errorTask;

            if (!completed)
            {
                process.Kill();
                _logger.LogError("OwnPriceSync zaman aşımına uğradı ({Timeout}s). stderr: {Error}",
                    timeoutMs / 1000, error);
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
        catch (Exception ex)
        {
            _logger.LogError(ex, "OwnPriceSyncJob çalıştırılırken beklenmeyen hata oluştu.");
        }
    }
}
