using Altin_Fiyat_Takip_Analizi.Application.Common;
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
    private readonly IRepository<SellerProduct> _sellerProductRepo;

    public PriceComparisonService(
        IRepository<PriceHistory> priceRepo,
        IRepository<Product> productRepo,
        IRepository<OwnPriceBySource> ownPriceRepo,
        IRepository<Seller> sellerRepo,
        IRepository<SellerProduct> sellerProductRepo)
    {
        _priceRepo = priceRepo;
        _productRepo = productRepo;
        _ownPriceRepo = ownPriceRepo;
        _sellerRepo = sellerRepo;
        _sellerProductRepo = sellerProductRepo;
    }

    public async Task<PriceComparisonDto> ComparePricesAsync(int productId, SellerType? sellerType = null)
    {
        var product = await _productRepo.GetByIdAsync(productId)
            ?? throw new NotFoundException($"Ürün bulunamadı: {productId}");

        // sellerType belirtildiyse o kaynağa özel OurPrice'ı kullan,
        // bulunamazsa (henüz senkronize edilmemişse) Product.OurPrice'a düş.        
        var sourcePrice = await _ownPriceRepo.GetQueryable()
            .FirstOrDefaultAsync(o => o.ProductId == productId && o.SourceType == SellerType.Bank);
        var storedPrice = sourcePrice?.Price ?? product.OurPrice;
        var allProducts = await _productRepo.GetAllAsync();
        var ownPrices = await _ownPriceRepo.GetQueryable()
            .Where(o => o.SourceType == SellerType.Bank)
            .ToListAsync();
        decimal ourPrice = GramPriceHelper.ResolveOurPrice(
            product,
            storedPrice,
            allProducts,
            id => ownPrices.FirstOrDefault(o => o.ProductId == id)?.Price);

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
        var ownPrices = await _ownPriceRepo.GetQueryable()
            .Where(o => o.SourceType == SellerType.Bank)
            .ToListAsync();
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
            var sourcePrice = ownPrices.FirstOrDefault(o => o.ProductId == product.Id);
            var storedPrice = sourcePrice?.Price ?? product.OurPrice;
            var ourPrice = GramPriceHelper.ResolveOurPrice(
                product,
                storedPrice,
                products,
                id => ownPrices.FirstOrDefault(o => o.ProductId == id)?.Price);

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

    public async Task<List<SellerProductBreakdownDto>> GetSellerProductBreakdownAsync(SellerType sellerType, string? platform = null)
    {
        // 1. İlgili platforma ve satıcı tipine uyan eşleşmiş ürünleri çek (küçük tablo, çok hızlı indexli sorgu)
        var spQuery = _sellerProductRepo.GetQueryable()
            .AsNoTracking()
            .Include(sp => sp.Seller)
            .Include(sp => sp.Product)
            .Where(sp => sp.IsActive && sp.IsMatched && sp.ProductId != null && sp.Seller.Type == sellerType && sp.Seller.IsActive);

        if (!string.IsNullOrWhiteSpace(platform))
        {
            var normalizedPlatform = platform.Trim().ToLowerInvariant();
            if (normalizedPlatform == "n11")
                spQuery = spQuery.Where(sp => sp.ExternalUrl.Contains("n11.com"));
            else if (normalizedPlatform == "pttavm")
                spQuery = spQuery.Where(sp => sp.ExternalUrl.Contains("pttavm.com"));
            else if (normalizedPlatform == "pazarama")
                spQuery = spQuery.Where(sp => sp.ExternalUrl.Contains("pazarama.com"));
            else
                spQuery = spQuery.Where(sp => sp.ExternalUrl.Contains(normalizedPlatform));
        }

        var matchedSellerProducts = await spQuery.ToListAsync();
        if (!matchedSellerProducts.Any()) return new List<SellerProductBreakdownDto>();

        var spMap = matchedSellerProducts.ToDictionary(sp => sp.Id);
        var spIds = spMap.Keys.ToList();

        var last24h = DateTime.UtcNow.AddHours(-24);

        // 2. Sadece bu SellerProductId'ler için son 24 saatteki en son fiyatları çek (En yüksek Id = en son kayıt)
        var maxPriceRecords = await _priceRepo.GetQueryable()
            .AsNoTracking()
            .Where(p => spIds.Contains(p.SellerProductId) && p.CollectedAt >= last24h && p.IsAvailable)
            .GroupBy(p => p.SellerProductId)
            .Select(g => new
            {
                SellerProductId = g.Key,
                MaxId = g.Max(p => p.Id)
            })
            .ToListAsync();

        var maxIds = maxPriceRecords.Select(x => x.MaxId).ToList();

        var latestPriceList = await _priceRepo.GetQueryable()
            .AsNoTracking()
            .Where(p => maxIds.Contains(p.Id))
            .Select(p => new { p.SellerProductId, p.Price, p.CollectedAt })
            .ToListAsync();

        // 3. OwnPrice'ları toplu çek
        var ownPrices = await _ownPriceRepo.GetQueryable()
            .AsNoTracking()
            .Where(o => o.SourceType == SellerType.Bank)
            .ToListAsync();

        // 4. Products'ı toplu çek (fallback OurPrice için)
        var products = (await _productRepo.GetAllAsync()).Where(p => p.IsActive).ToDictionary(p => p.Id);

        var result = new List<SellerProductBreakdownDto>();

        // Satıcı bazında grupla
        var productsBySeller = matchedSellerProducts
            .GroupBy(sp => sp.SellerId);

        var priceBySpId = latestPriceList
            .Where(lp => lp != null)
            .ToDictionary(lp => lp!.SellerProductId, lp => lp!);

        foreach (var sellerGroup in productsBySeller)
        {
            var seller = sellerGroup.First().Seller;
            var dto = new SellerProductBreakdownDto
            {
                SellerId = seller.Id,
                SellerName = seller.Name
            };

            foreach (var sp in sellerGroup.OrderBy(sp => sp.Product?.Name))
            {
                if (!priceBySpId.TryGetValue(sp.Id, out var latestPrice))
                    continue;

                var productId = sp.ProductId!.Value;
                var product = products.GetValueOrDefault(productId);
                if (product == null) continue;

                // Bizim fiyatımız: önce OwnPriceBySource, yoksa Product.OurPrice
                var ownPrice = ownPrices.FirstOrDefault(o => o.ProductId == productId);
                var storedPrice = ownPrice?.Price ?? product.OurPrice;
                var ourPrice = GramPriceHelper.ResolveOurPrice(
                    product,
                    storedPrice,
                    products.Values,
                    id => ownPrices.FirstOrDefault(o => o.ProductId == id)?.Price);

                var sellerPrice = latestPrice.Price;
                var diff = ourPrice - sellerPrice;
                var diffPercent = sellerPrice > 0 ? (diff / sellerPrice) * 100 : 0;

                dto.Products.Add(new SellerProductComparisonDto
                {
                    SellerProductId = sp.Id,
                    SellerName = seller.Name,
                    ExternalProductName = sp.ExternalName,
                    ExternalUrl = sp.ExternalUrl,
                    MatchedProductId = productId,
                    MatchedProductName = product.Name,
                    SellerPrice = sellerPrice,
                    OurPrice = ourPrice,
                    PriceDiff = diff,
                    PriceDiffPercent = Math.Round(diffPercent, 2),
                    CollectedAt = latestPrice.CollectedAt
                });
            }

            // Aynı ürün URL'sine ait mükerrer varyant varsa sadece en son tarananı koru
            if (dto.Products.Any())
            {
                dto.Products = dto.Products
                    .GroupBy(p => {
                        var url = p.ExternalUrl ?? "";
                        var qIdx = url.IndexOf('?');
                        return qIdx > 0 ? url.Substring(0, qIdx) : url;
                    })
                    .Select(g => g.OrderByDescending(p => p.CollectedAt).First())
                    .ToList();

                result.Add(dto);
            }
        }

        return result;
    }

}
