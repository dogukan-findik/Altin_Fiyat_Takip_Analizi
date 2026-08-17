using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace Altin_Fiyat_Takip_Analizi.Application.Services;

public class PriceAlertService : IPriceAlertService
{
    private readonly IRepository<PriceAlert> _alertRepo;

    public PriceAlertService(IRepository<PriceAlert> alertRepo)
    {
        _alertRepo = alertRepo;
    }

    public async Task<List<int>> GetTriggeredAlertIdsAsync(int productId, decimal currentPrice)
    {
        var alerts = await _alertRepo.GetQueryable()
            .Where(a => a.ProductId == productId && a.IsActive)
            .ToListAsync();

        return alerts.Where(a => a.ThresholdType switch
        {
            "Below" => currentPrice < a.ThresholdValue,
            "Above" => currentPrice > a.ThresholdValue,
            _ => false // "PercentChange" için önceki fiyata ihtiyaç var, ileri seviye — şimdilik desteklenmiyor
        }).Select(a => a.Id).ToList();
    }
}