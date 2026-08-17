using Altin_Fiyat_Takip_Analizi.Application.DTOs;

namespace Altin_Fiyat_Takip_Analizi.Application.Interfaces
{
    public interface ISellerService
    {
        Task<List<SellerDto>> GetAllAsync();
        Task<SellerDto?> GetByIdAsync(int id);
        Task<SellerDto> CreateAsync(SellerDto dto);
        Task UpdateAsync(int id, SellerDto dto);
        Task DeleteAsync(int id);
        Task<List<SellerProductDto>> GetSellerProductsAsync(int sellerId);
    }
}
