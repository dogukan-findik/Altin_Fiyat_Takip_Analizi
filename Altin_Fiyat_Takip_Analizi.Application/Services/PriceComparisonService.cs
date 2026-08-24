using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Altin_Fiyat_Takip_Analizi.Application.Exceptions;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Altin_Fiyat_Takip_Analizi.Domain.Enums;
using Microsoft.EntityFrameworkCore;

namespace Altin_Fiyat_Takip_Analizi.Application.Services;

public class PriceComparisonService : IPriceComparisonService
{
    private readonly IRepository<PriceHistory> _priceRepo;
    private readonly IRepository<Product> _productRepo;
    private readonly IRepository<OwnPriceBySource> _ownPriceRepo;
    private readonly IRepository<Seller> _sellerRepo;


    public PriceComparisonService(
        IRepository<PriceHistory> priceRepo,
        IRepository<Product> productRepo,
        IRepository<OwnPriceBySource> ownPriceRepo,
        IRepository<Seller> sellerRepo)
    {
        _priceRepo = priceRepo;
        _productRepo = productRepo;
        _ownPriceRepo = ownPriceRepo;
        _sellerRepo = sellerRepo;
    }

    public async Task<PriceComparisonDto> ComparePricesAsync(int productId, SellerType? sellerType = null)
    {
        var product = await _productRepo.GetByIdAsync(productId)
            ?? throw new NotFoundException($"Ürün bulunamadı: {productId}");

        // sellerType belirtildiyse o kaynağa özel OurPrice'ı kullan,
        // bulunamazsa (henüz senkronize edilmemişse) Product.OurPrice'a düş.        
        var sourcePrice = await _ownPriceRepo.GetQueryable()
            .FirstOrDefaultAsync(o => o.ProductId == productId && o.SourceType == SellerType.Bank);
        decimal ourPrice = sourcePrice?.Price ?? product.OurPrice; // son çare olarak eski donuk kolon

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
                OurPrice = ourPrice,
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
            OurPrice = ourPrice,
            CompetitorAvgPrice = avgPrice,
            MinPrice = minPrice.Price,
            MinPriceSeller = minPrice.SellerProduct.Seller.Name,
            MaxPrice = maxPrice.Price,
            MaxPriceSeller = maxPrice.SellerProduct.Seller.Name,
            DiffFromAvg = ourPrice - avgPrice,
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

    public async Task<List<ProductSellerBreakdownDto>> GetSellerBreakdownAsync(SellerType sellerType)
    {
        var products = (await _productRepo.GetAllAsync()).Where(p => p.IsActive).ToList();
        var sellers = await _sellerRepo.GetQueryable()
            .Where(s => s.Type == sellerType && s.IsActive)
            .ToListAsync();

        var last24h = DateTime.UtcNow.AddHours(-24);

        var latestPrices = await _priceRepo.GetQueryable()
            .Include(p => p.SellerProduct)
            .Where(p => p.CollectedAt >= last24h
                        && p.IsAvailable
                        && p.SellerProduct.Seller.Type == sellerType
                        && p.SellerProduct.ProductId != null)
            .GroupBy(p => new { p.SellerProduct.SellerId, p.SellerProduct.ProductId })
            .Select(g => g.OrderByDescending(p => p.CollectedAt).First())
            .ToListAsync();

        var result = new List<ProductSellerBreakdownDto>();

        foreach (var product in products)
        {
            var sourcePrice = await _ownPriceRepo.GetQueryable()
                .FirstOrDefaultAsync(o => o.ProductId == product.Id && o.SourceType == SellerType.Bank);
            var ourPrice = sourcePrice?.Price ?? product.OurPrice;

            var dto = new ProductSellerBreakdownDto
            {
                ProductId = product.Id,
                ProductName = product.Name,
                OurPrice = ourPrice
            };

            foreach (var seller in sellers)
            {
                var match = latestPrices.FirstOrDefault(p =>
                    p.SellerProduct.SellerId == seller.Id && p.SellerProduct.ProductId == product.Id);

                dto.SellerPrices.Add(new SellerPriceEntryDto
                {
                    SellerId = seller.Id,
                    SellerName = seller.Name,
                    Price = match?.Price,
                    DiffFromOurs = match is not null ? ourPrice - match.Price : null
                });
            }

            result.Add(dto);
        }

        return result;
    }

    public async Task<List<SellerProductBreakdownDto>> GetSellerProductBreakdownAsync(SellerType sellerType)
    {
        var sellers = await _sellerRepo.GetQueryable()
            .Where(s => s.Type == sellerType && s.IsActive)
            .ToListAsync();

        var last24h = DateTime.UtcNow.AddHours(-24);

        // Son 24 saat içindeki tüm fiyatları çek (her sellerProduct için en son fiyat)
        var latestPrices = await _priceRepo.GetQueryable()
            .Include(p => p.SellerProduct)
                .ThenInclude(sp => sp.Seller)
            .Include(p => p.SellerProduct)
                .ThenInclude(sp => sp.Product)
            .Where(p => p.CollectedAt >= last24h
                        && p.IsAvailable
                        && p.SellerProduct.Seller.Type == sellerType
                        && p.SellerProduct.ProductId != null
                        && p.SellerProduct.IsMatched)
            .GroupBy(p => p.SellerProductId)
            .Select(g => g.OrderByDescending(p => p.CollectedAt).First())
            .ToListAsync();

        // OwnPrice'ları toplu çek
        var ownPrices = await _ownPriceRepo.GetQueryable()
            .Where(o => o.SourceType == SellerType.Bank)
            .ToListAsync();

        // Products'ı toplu çek (fallback OurPrice için)
        var products = (await _productRepo.GetAllAsync()).Where(p => p.IsActive).ToDictionary(p => p.Id);

        var result = new List<SellerProductBreakdownDto>();

        foreach (var seller in sellers)
        {
            var sellerPrices = latestPrices
                .Where(p => p.SellerProduct.SellerId == seller.Id)
                .OrderBy(p => p.SellerProduct.Product?.Name)
                .ToList();

            if (!sellerPrices.Any()) continue;

            var dto = new SellerProductBreakdownDto
            {
                SellerId = seller.Id,
                SellerName = seller.Name
            };

            foreach (var ph in sellerPrices)
            {
                var productId = ph.SellerProduct.ProductId!.Value;
                var product = products.GetValueOrDefault(productId);
                if (product == null) continue;

                // Bizim fiyatımız: önce OwnPriceBySource, yoksa Product.OurPrice
                var ownPrice = ownPrices.FirstOrDefault(o => o.ProductId == productId);
                var ourPrice = ownPrice?.Price ?? product.OurPrice;

                var diff = ourPrice - ph.Price;
                var diffPercent = ph.Price != 0 ? (diff / ph.Price) * 100 : 0;

                dto.Products.Add(new SellerProductComparisonDto
                {
                    SellerProductId = ph.SellerProduct.Id,
                    SellerName = seller.Name,
                    ExternalProductName = ph.SellerProduct.ExternalName,
                    ExternalUrl = ph.SellerProduct.ExternalUrl,
                    SellerPrice = ph.Price,
                    MatchedProductId = productId,
                    MatchedProductName = product.Name,
                    OurPrice = ourPrice,
                    PriceDiff = diff,
                    PriceDiffPercent = Math.Round(diffPercent, 2),
                    CollectedAt = ph.CollectedAt
                });
            }

            if (dto.Products.Any())
                result.Add(dto);
        }

        return result;
    }

}
