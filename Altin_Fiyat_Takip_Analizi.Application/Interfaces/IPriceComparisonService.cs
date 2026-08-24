using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Altin_Fiyat_Takip_Analizi.Domain.Enums;

namespace Altin_Fiyat_Takip_Analizi.Application.Interfaces;

public interface IPriceComparisonService
{
    Task<PriceComparisonDto> ComparePricesAsync(int productId, SellerType? sellerType = null);
    Task<List<PriceComparisonDto>> GetAllComparisonsAsync(SellerType? sellerType = null);

    Task<List<ProductSellerBreakdownDto>> GetSellerBreakdownAsync(SellerType sellerType);

    /// <summary>
    /// Satıcıların her bir ürününü bizim fiyatımızla tek tek karşılaştırır.
    /// Satıcı bazlı gruplandırılmış, ürün bazlı detaylı karşılaştırma.
    /// </summary>
    Task<List<SellerProductBreakdownDto>> GetSellerProductBreakdownAsync(SellerType sellerType);
}
