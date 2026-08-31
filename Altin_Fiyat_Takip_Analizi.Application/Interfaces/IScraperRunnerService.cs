namespace Altin_Fiyat_Takip_Analizi.Application.Interfaces;

public interface IScraperRunnerService
{
    /// <summary>
    /// Belirtilen platform için Python scraper'ını tetikler (n11, pttavm, pazarama, own, all).
    /// force = true ise throttle süresi beklenmez.
    /// waitForRunning = true ise halen çalışan bir tarama varsa bitmesi beklenir.
    /// </summary>
    Task<bool> TriggerScrapeAsync(string platform, bool force = false, bool waitForRunning = false);

    /// <summary>
    /// Belirtilen platform için şu an aktif bir tarama işlemi sürüyor mu?
    /// </summary>
    bool IsScraping(string platform);

    /// <summary>
    /// Belirtilen platformun en son ne zaman tarandığı zamanı döner.
    /// </summary>
    DateTime? GetLastScrapedAt(string platform);
}
