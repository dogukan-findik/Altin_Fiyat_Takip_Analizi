using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Altin_Fiyat_Takip_Analizi.Domain.Enums;

namespace Altin_Fiyat_Takip_Analizi.Domain.Entities;

public class OwnPriceBySource
{
    public int Id { get; set; }
    public int ProductId { get; set; }
    public SellerType SourceType { get; set; } // Bank = ahlatcidoviz/ahlatcistore, Marketplace = n11
    public decimal Price { get; set; }
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    public Product Product { get; set; } = null!;
}