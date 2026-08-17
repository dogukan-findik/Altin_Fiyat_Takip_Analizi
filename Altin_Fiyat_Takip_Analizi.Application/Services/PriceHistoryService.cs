using Microsoft.EntityFrameworkCore;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;

namespace Altin_Fiyat_Takip_Analizi.Application.Services;

public class PriceHistoryService : IPriceHistoryService
{
    private readonly IRepository<PriceHistory> _priceRepo;
    private readonly IRepository<Product> _productRepo;
    private readonly IRepository<Seller> _sellerRepo;


    public PriceHistoryService(IRepository<PriceHistory> priceRepo, IRepository<Product> productRepo, IRepository<Seller> sellerRepo)
    {
        _priceRepo = priceRepo;
        _productRepo = productRepo;
        _sellerRepo = sellerRepo;
    }
    public async Task<List<PriceHistoryDto>> GetForProductAsync(int productId, int days = 30)
    {
        var since = DateTime.UtcNow.AddDays(-days);
        return await BaseQuery()
            .Where(p => p.SellerProduct.ProductId == productId && p.CollectedAt >= since)
            .OrderByDescending(p => p.CollectedAt)
            .Select(ToDto())
            .ToListAsync();
    }

    public async Task<List<PriceHistoryDto>> GetFilteredAsync(PriceHistoryFilterDto filter)
    {
        var query = BaseQuery();

        if (filter.ProductId.HasValue)
            query = query.Where(p => p.SellerProduct.ProductId == filter.ProductId);

        if (filter.SellerId.HasValue)
            query = query.Where(p => p.SellerProduct.SellerId == filter.SellerId);

        if (filter.From.HasValue)
            query = query.Where(p => p.CollectedAt >= filter.From);

        if (filter.To.HasValue)
            query = query.Where(p => p.CollectedAt <= filter.To);

        return await query.OrderByDescending(p => p.CollectedAt).Select(ToDto()).ToListAsync();
    }

    public async Task<List<PriceHistoryDto>> GetLatestAsync()
    {
        return await BaseQuery()
            .GroupBy(p => p.SellerProductId)
            .Select(g => g.OrderByDescending(p => p.CollectedAt).First())
            .Select(ToDto())
            .ToListAsync();
    }

    public async Task<PriceHistoryStatsDto> GetStatsAsync()
    {
        var all = await _priceRepo.GetAllAsync();

        return new PriceHistoryStatsDto
        {
            TotalRecords = all.Count,
            TotalProductsTracked = (await _productRepo.GetAllAsync()).Count(p => p.IsActive),
            TotalSellersActive = (await _sellerRepo.GetAllAsync()).Count(s => s.IsActive),
            OldestRecord = all.MinBy(p => p.CollectedAt)?.CollectedAt,
            NewestRecord = all.MaxBy(p => p.CollectedAt)?.CollectedAt
        };
    }

    private IQueryable<PriceHistory> BaseQuery() =>
        _priceRepo.GetQueryable()
            .Include(p => p.SellerProduct)
                .ThenInclude(sp => sp.Seller);

    private static System.Linq.Expressions.Expression<Func<PriceHistory, PriceHistoryDto>> ToDto() =>
        p => new PriceHistoryDto
        {
            Id = p.Id,
            SellerProductId = p.SellerProductId,
            SellerName = p.SellerProduct.Seller.Name,
            Price = p.Price,
            Currency = p.Currency,
            IsAvailable = p.IsAvailable,
            CollectedAt = p.CollectedAt
        };

}

