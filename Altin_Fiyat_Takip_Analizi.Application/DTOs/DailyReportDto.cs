namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class DailyReportDto
{
    public DateOnly ReportDate { get; set; }
    public List<PriceComparisonDto> Comparisons { get; set; } = new();
    public int TotalProductsTracked { get; set; }
    public int TotalSellersActive { get; set; }
}