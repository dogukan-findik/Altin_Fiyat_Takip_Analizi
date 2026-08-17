using Microsoft.Extensions.Logging;
using Quartz;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;

namespace Altin_Fiyat_Takip_Analizi.Scheduler.Jobs;

public class DailyReportJob : IJob
{
    private readonly IReportService _reportService;
    private readonly ILogger<DailyReportJob> _logger;

    public DailyReportJob(IReportService reportService, ILogger<DailyReportJob> logger)
    {
        _reportService = reportService;
        _logger = logger;
    }

    public async Task Execute(IJobExecutionContext context)
    {
        var today = DateOnly.FromDateTime(DateTime.UtcNow);
        try
        {
            var report = await _reportService.GenerateDailyReportAsync(today);
            _logger.LogInformation("Günlük rapor üretildi: {Date}, {Count} ürün.",
                today, report.TotalProductsTracked);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "DailyReportJob hata ile sonlandı: {Date}", today);
        }
    }
}