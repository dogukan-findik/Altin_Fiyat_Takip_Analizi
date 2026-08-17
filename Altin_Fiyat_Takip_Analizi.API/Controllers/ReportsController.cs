using Microsoft.AspNetCore.Mvc;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Microsoft.AspNetCore.Authorization;

namespace Altin_Fiyat_Takip_Analizi.API.Controllers;

[ApiController]
[Route("api/v1/reports")]
[Authorize]
public class ReportsController : ControllerBase
{
    private readonly IReportService _reportService;

    public ReportsController(IReportService reportService)
    {
        _reportService = reportService;
    }

    [HttpGet("daily/{date:datetime}")]
    public async Task<ActionResult<DailyReportDto>> GetDaily(DateTime date)
    {
        var report = await _reportService.GetReportByDateAsync(DateOnly.FromDateTime(date));
        return report is null ? NotFound() : Ok(report);
    }

    [HttpPost("daily/{date:datetime}/generate")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<DailyReportDto>> GenerateDaily(DateTime date)
    {
        var report = await _reportService.GenerateDailyReportAsync(DateOnly.FromDateTime(date));
        return Ok(report);
    }

    [HttpGet("weekly")]
    public async Task<ActionResult<List<DailyReportDto>>> GetWeekly([FromQuery] DateTime? weekEndDate = null)
    {
        var endDate = weekEndDate.HasValue
            ? DateOnly.FromDateTime(weekEndDate.Value)
            : DateOnly.FromDateTime(DateTime.UtcNow);

        var summary = await _reportService.GetWeeklySummaryAsync(endDate);
        return Ok(summary);
    }
}
