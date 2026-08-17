

using Altin_Fiyat_Takip_Analizi.Application.DTOs;

namespace Altin_Fiyat_Takip_Analizi.Application.Interfaces;

public interface ISellerProductService
{
    Task<List<SellerProductDto>> GetAllAsync();
    Task<SellerProductDto> CreateAsync(CreateSellerProductDto dto);
    Task UpdateMatchAsync(int id, UpdateMatchDto dto);
    Task<List<AutoMatchResultDto>> AutoMatchAsync(decimal thresholdPercent = 80);
}
