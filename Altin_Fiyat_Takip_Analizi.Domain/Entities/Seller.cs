using Altin_Fiyat_Takip_Analizi.Domain.Enums;

namespace Altin_Fiyat_Takip_Analizi.Domain.Entities;

public class Seller
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? WebsiteUrl { get; set; }
    public string? LogoUrl { get; set; }
    public bool IsActive { get; set; } = true;
    public SellerType Type { get; set; } = SellerType.Bank;
    public string? ScrapingConfig { get; set; } // JSON: selector'lar, URL pattern'leri
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
   

    public ICollection<SellerProduct> SellerProducts { get; set; } = new List<SellerProduct>();
}