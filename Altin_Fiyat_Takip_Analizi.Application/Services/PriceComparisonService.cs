using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Altin_Fiyat_Takip_Analizi.Domain.Enums;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Altin_Fiyat_Takip_Analizi.Application.Exceptions;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace Altin_Fiyat_Takip_Analizi.Application.Services;

public class PriceComparisonService : IPriceComparisonService
{
    private readonly IRepository<PriceHistory> _priceRepo;
    private readonly IRepository<Product> _productRepo;

    public PriceComparisonService(IRepository<PriceHistory> priceRepo, IRepository<Product> productRepo)
    {
        _priceRepo = priceRepo;
        _productRepo = productRepo;
    }

    public async Task<PriceComparisonDto> ComparePricesAsync(int productId, SellerType? sellerType = null)
    {
        var product = await _productRepo.GetByIdAsync(productId)
            ?? throw new NotFoundException($"Ürün bulunamadı: {productId}");

        var last24h = DateTime.UtcNow.AddHours(-24);

        var query = _priceRepo.GetQueryable()
            .Include(p => p.SellerProduct)
                .ThenInclude(sp => sp.Seller)
            .Where(p => p.SellerProduct.ProductId == productId
                        && p.CollectedAt >= last24h
                        && p.IsAvailable);

        if (sellerType.HasValue)
            query = query.Where(p => p.SellerProduct.Seller.Type == sellerType.Value);

        var latestPrices = await query
            .GroupBy(p => p.SellerProduct.SellerId)
            .Select(g => g.OrderByDescending(p => p.CollectedAt).First())
            .ToListAsync();

        if (!latestPrices.Any())
        {
            return new PriceComparisonDto
            {
                ProductId = productId,
                ProductName = product.Name,
                OurPrice = product.OurPrice,
                CalculatedAt = DateTime.UtcNow
            };
        }

        var avgPrice = latestPrices.Average(p => p.Price);
        var minPrice = latestPrices.MinBy(p => p.Price)!;
        var maxPrice = latestPrices.MaxBy(p => p.Price)!;

        return new PriceComparisonDto
        {
            ProductId = productId,
            ProductName = product.Name,
            OurPrice = product.OurPrice,
            CompetitorAvgPrice = avgPrice,
            MinPrice = minPrice.Price,
            MinPriceSeller = minPrice.SellerProduct.Seller.Name,
            MaxPrice = maxPrice.Price,
            MaxPriceSeller = maxPrice.SellerProduct.Seller.Name,
            DiffFromAvg = product.OurPrice - avgPrice,
            CalculatedAt = DateTime.UtcNow
        };
    }

    public async Task<List<PriceComparisonDto>> GetAllComparisonsAsync(SellerType? sellerType = null)
    {
        var products = await _productRepo.GetAllAsync();
        var results = new List<PriceComparisonDto>();

        foreach (var product in products.Where(p => p.IsActive))
            results.Add(await ComparePricesAsync(product.Id, sellerType));

        return results;
    }
}