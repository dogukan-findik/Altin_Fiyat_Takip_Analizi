namespace Altin_Fiyat_Takip_Analizi.Domain.Entities;

public class SellerProduct
{
    public int Id { get; set; }
    public int SellerId { get; set; }
    public int? ProductId { get; set; } // null = henüz eşleşmemiş

    public string ExternalName { get; set; } = string.Empty;
    public string ExternalUrl { get; set; } = string.Empty;
    public string? ExternalId { get; set; }

    public bool IsMatched { get; set; } = false;
    public decimal? MatchConfidence { get; set; } // 0-100
    public bool IsActive { get; set; } = true;
    public DateTime? LastCollectedAt { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Seller Seller { get; set; } = null!;
    public Product? Product { get; set; }
    public ICollection<PriceHistory> PriceHistories { get; set; } = new List<PriceHistory>();
}