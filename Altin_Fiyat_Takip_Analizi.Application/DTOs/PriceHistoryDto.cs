namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class PriceHistoryDto
{
    public long Id { get; set; }
    public int SellerProductId { get; set; }
    public decimal Price { get; set; }
    public string SellerName { get; set; } = string.Empty;
    public string Currency { get; set; } = "TRY";
    public bool IsAvailable { get; set; }
    public DateTime CollectedAt { get; set; }
}