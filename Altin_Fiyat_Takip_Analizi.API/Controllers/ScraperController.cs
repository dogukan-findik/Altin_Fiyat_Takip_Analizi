using Microsoft.AspNetCore.Mvc;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;

namespace Altin_Fiyat_Takip_Analizi.API.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
public class ScraperController : ControllerBase
{
    private readonly IScraperRunnerService _scraperRunner;
    private readonly ILogger<ScraperController> _logger;

    public ScraperController(IScraperRunnerService scraperRunner, ILogger<ScraperController> logger)
    {
        _scraperRunner = scraperRunner;
        _logger = logger;
    }

    /// <summary>
    /// Belirtilen platform için anlık canlı tarama tetikler (n11, pttavm, pazarama, all).
    /// </summary>
    [HttpPost("trigger")]
    public async Task<IActionResult> TriggerScrape(
        [FromQuery] string platform = "all",
        [FromQuery] bool force = false,
        [FromQuery] bool wait = false)
    {
        if (wait)
        {
            // Taramanın bitmesini bekle ve sonucu dön
            var success = await _scraperRunner.TriggerScrapeAsync(platform, force, waitForRunning: true);
            return Ok(new
            {
                Platform = platform,
                Success = success,
                Message = success ? "Tarama başarıyla tamamlandı." : "Tarama başarısız oldu veya atlandı."
            });
        }

        // Arka planda başlat ve hemen 202 Accepted dön (UI donmasın)
        _ = Task.Run(async () =>
        {
            try
            {
                await _scraperRunner.TriggerScrapeAsync(platform, force);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Arka plan canlı tarama hatası: {Platform}", platform);
            }
        });

        return Accepted(new
        {
            Platform = platform,
            Status = "Started",
            Message = "Canlı tarama arka planda başlatıldı."
        });
    }

    /// <summary>
    /// Platformun tarama durumunu ve son tarama zamanını sorgular.
    /// </summary>
    [HttpGet("status")]
    public IActionResult GetStatus([FromQuery] string platform = "all")
    {
        var isScraping = _scraperRunner.IsScraping(platform);
        var lastScrapedAt = _scraperRunner.GetLastScrapedAt(platform);

        return Ok(new
        {
            Platform = platform,
            IsScraping = isScraping,
            LastScrapedAt = lastScrapedAt
        });
    }
}
