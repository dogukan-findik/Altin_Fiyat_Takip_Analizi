namespace Altin_Fiyat_Takip_Analizi.Domain.Entities;

public class PriceHistory
{
    public long Id { get; set; }
    public int SellerProductId { get; set; }
    public decimal Price { get; set; }
    public string Currency { get; set; } = "TRY";
    public bool IsAvailable { get; set; } = true; // stokta var mı?
    public DateTime CollectedAt { get; set; } = DateTime.UtcNow;
    public int? CollectionJobId { get; set; }

    public SellerProduct SellerProduct { get; set; } = null!;
}