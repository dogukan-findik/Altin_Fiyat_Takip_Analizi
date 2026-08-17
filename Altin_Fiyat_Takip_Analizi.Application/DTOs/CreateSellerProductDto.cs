namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class CreateSellerProductDto
{
    public int SellerId { get; set; }
    public string ExternalName { get; set; } = string.Empty;
    public string ExternalUrl { get; set; } = string.Empty;
    public string? ExternalId { get; set; }
    public int? ProductId { get; set; } // biliniyorsa manuel eşleştirme direkt burada yapılır
}