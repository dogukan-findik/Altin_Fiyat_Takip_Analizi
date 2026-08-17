namespace Altin_Fiyat_Takip_Analizi.Application.Interfaces;

public interface IPriceAlertService
{
    Task<List<int>> GetTriggeredAlertIdsAsync(int productId, decimal currentPrice);
}