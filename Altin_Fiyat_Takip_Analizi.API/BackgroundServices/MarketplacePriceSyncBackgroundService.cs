using Altin_Fiyat_Takip_Analizi.Application.Interfaces;

namespace Altin_Fiyat_Takip_Analizi.API.BackgroundServices;

/// <özet>
/// API process'i ayakta olduğu sürece her 2 dakikada bir
/// pazaryeri fiyatlarını (Pazarama, N11, PTTAVM) sırayla tarayarak
/// sistemdeki tüm pazaryeri altın fiyatlarının her daim güncel kalmasını sağlar.
/// </özet>
public class MarketplacePriceSyncBackgroundService : BackgroundService
{
    private readonly IScraperRunnerService _scraperRunner;
    private readonly ILogger<MarketplacePriceSyncBackgroundService> _logger;

    // Her 2 dakikada bir otomatik döngü
    private static readonly TimeSpan Interval = TimeSpan.FromMinutes(2);

    public MarketplacePriceSyncBackgroundService(
        IScraperRunnerService scraperRunner,
        ILogger<MarketplacePriceSyncBackgroundService> logger)
    {
        _scraperRunner = scraperRunner;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation(
            "MarketplacePriceSyncBackgroundService başlatıldı — her {Minutes} dakikada bir çalışacak.",
            Interval.TotalMinutes);

        // API'nin ve veritabanının tam hazır olması için başlangıçta 2 saniye bekle
        try
        {
            await Task.Delay(TimeSpan.FromSeconds(2), stoppingToken);
        }
        catch (OperationCanceledException)
        {
            return;
        }

        // İlk periyodik taramayı yap (try-catch ile uygulama kapanmasını önle)
        try
        {
            await RunMarketplaceSyncAsync(stoppingToken);
        }
        catch (Exception ex) when (!stoppingToken.IsCancellationRequested)
        {
            _logger.LogError(ex, "İlk pazaryeri senkronizasyonunda hata oluştu.");
        }

        using var timer = new PeriodicTimer(Interval);
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await timer.WaitForNextTickAsync(stoppingToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }

            try
            {
                await RunMarketplaceSyncAsync(stoppingToken);
            }
            catch (Exception ex) when (!stoppingToken.IsCancellationRequested)
            {
                _logger.LogError(ex, "Periyodik pazaryeri senkronizasyonunda hata oluştu.");
            }
        }

        _logger.LogInformation("MarketplacePriceSyncBackgroundService durduruldu.");
    }

    private async Task RunMarketplaceSyncAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Pazaryeri otomatik fiyat senkronizasyonu başlatılıyor...");

        // Pazaryerlerini sırayla tara (N11 -> PTTAVM -> Pazarama)
        string[] platforms = { "n11", "pttavm", "pazarama" };

        foreach (var platform in platforms)
        {
            if (stoppingToken.IsCancellationRequested) break;

            try
            {
                _logger.LogInformation("Otomatik pazaryeri taraması: [{Platform}]", platform);
                await _scraperRunner.TriggerScrapeAsync(platform, force: true);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Otomatik pazaryeri tarama hatası: [{Platform}]", platform);
            }

            // Platformlar arası kısa nefes alma
            try
            {
                await Task.Delay(TimeSpan.FromSeconds(5), stoppingToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }

        _logger.LogInformation("Pazaryeri otomatik fiyat senkronizasyonu tamamlandı.");
    }
}
