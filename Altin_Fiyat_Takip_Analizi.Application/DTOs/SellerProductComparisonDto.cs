namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

/// <summary>
/// Bir satıcının tek bir ürünü ile bizim fiyatımızın karşılaştırması
/// </summary>
public class SellerProductComparisonDto
{
    public int SellerProductId { get; set; }
    public string SellerName { get; set; } = string.Empty;
    public string ExternalProductName { get; set; } = string.Empty;
    public string? ExternalUrl { get; set; }
    public decimal SellerPrice { get; set; }

    // Bizim eşleşen ürünümüz
    public int? MatchedProductId { get; set; }
    public string MatchedProductName { get; set; } = string.Empty;
    public decimal OurPrice { get; set; }

    // Fark: pozitif = biz pahalıyız, negatif = biz ucuzuz
    public decimal PriceDiff { get; set; }
    public decimal PriceDiffPercent { get; set; }

    public DateTime CollectedAt { get; set; }
}

/// <summary>
/// Satıcı bazlı gruplandırılmış ürün karşılaştırma sonuçları
/// </summary>
public class SellerProductBreakdownDto
{
    public int SellerId { get; set; }
    public string SellerName { get; set; } = string.Empty;
    public List<SellerProductComparisonDto> Products { get; set; } = new();
}
