namespace Altin_Fiyat_Takip_Analizi.Domain.Entities;

public class DailyReport
{
    public int Id { get; set; }
    public DateOnly ReportDate { get; set; }
    public int ProductId { get; set; }
    public decimal? OurPrice { get; set; }
    public decimal? CompetitorAvgPrice { get; set; }
    public decimal? MinPrice { get; set; }
    public decimal? MaxPrice { get; set; }
    public int? MinPriceSellerId { get; set; }
    public int? MaxPriceSellerId { get; set; }
    public decimal? PriceDiffFromAvg { get; set; }
    public int PriceChangeCount { get; set; }
    public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;

    public Product Product { get; set; } = null!;
    public Seller? MinPriceSeller { get; set; }
    public Seller? MaxPriceSeller { get; set; }
}