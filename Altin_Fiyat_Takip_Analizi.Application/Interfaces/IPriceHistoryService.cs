using Altin_Fiyat_Takip_Analizi.Application.DTOs;

namespace Altin_Fiyat_Takip_Analizi.Application.Interfaces;

public interface IPriceHistoryService
{
    Task<List<PriceHistoryDto>> GetForProductAsync(int productId, int days = 30);
    Task<List<PriceHistoryDto>> GetFilteredAsync(PriceHistoryFilterDto filter);
    Task<List<PriceHistoryDto>> GetLatestAsync();
    Task<PriceHistoryStatsDto> GetStatsAsync();
}