namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class PriceComparisonDto
{
    public int ProductId { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public decimal OurPrice { get; set; }
    public decimal CompetitorAvgPrice { get; set; }
    public decimal MinPrice { get; set; }
    public string MinPriceSeller { get; set; } = string.Empty;
    public decimal MaxPrice { get; set; }
    public string MaxPriceSeller { get; set; } = string.Empty;
    public decimal DiffFromAvg { get; set; }
    public DateTime CalculatedAt { get; set; }
}