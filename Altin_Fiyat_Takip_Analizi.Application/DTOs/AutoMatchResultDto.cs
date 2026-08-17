

namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class AutoMatchResultDto
{
    public int SellerProductId { get; set; }
    public string ExternalName { get; set; } = string.Empty;
    public int? MatchedProductId { get; set; }
    public string? MatchedProductName { get; set; }
    public decimal Confidence { get; set; }
    public bool Applied { get; set; } // eşik üstüyse true, altındaysa öneri olarak kalır
}
