using Altin_Fiyat_Takip_Analizi.Application.DTOs;

namespace Altin_Fiyat_Takip_Analizi.Application.Interfaces;

public interface IReportService
{
    Task<DailyReportDto> GenerateDailyReportAsync(DateOnly date);
    Task<DailyReportDto?> GetReportByDateAsync(DateOnly date);
    Task<List<DailyReportDto>> GetWeeklySummaryAsync(DateOnly weekEndDate);
}