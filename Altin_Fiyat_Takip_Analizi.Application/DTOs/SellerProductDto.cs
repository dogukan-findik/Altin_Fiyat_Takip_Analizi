namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class SellerProductDto
{
    public int Id { get; set; }
    public int SellerId { get; set; }
    public int? ProductId { get; set; }
    public string ExternalName { get; set; } = string.Empty;
    public string ExternalUrl { get; set; } = string.Empty;
    public bool IsMatched { get; set; }
    public decimal? MatchConfidence { get; set; }
    public bool IsActive { get; set; }
    public DateTime? LastCollectedAt { get; set; }
}