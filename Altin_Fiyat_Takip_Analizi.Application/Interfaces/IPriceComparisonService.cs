using Altin_Fiyat_Takip_Analizi.Application.DTOs;

namespace Altin_Fiyat_Takip_Analizi.Application.Interfaces;

public interface IPriceComparisonService
{
    Task<PriceComparisonDto> ComparePricesAsync(int productId);
    Task<List<PriceComparisonDto>> GetAllComparisonsAsync();
}