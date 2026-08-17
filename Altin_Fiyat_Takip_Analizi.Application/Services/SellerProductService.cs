using Microsoft.EntityFrameworkCore;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Altin_Fiyat_Takip_Analizi.Application.Exceptions;
using Altin_Fiyat_Takip_Analizi.Application.Common;

namespace Altin_Fiyat_Takip_Analizi.Application.Services;

public class SellerProductService : ISellerProductService
{
    private readonly IRepository<SellerProduct> _sellerProductRepo;
    private readonly IRepository<Product> _productRepo;
    public SellerProductService(IRepository<SellerProduct> sellerProductRepo, IRepository<Product> productRepo)
    {
        _sellerProductRepo = sellerProductRepo;
        _productRepo = productRepo;
    }
    public async Task<List<SellerProductDto>> GetAllAsync()
    {
        return await _sellerProductRepo.GetQueryable()
            .Select(sp => new SellerProductDto
            {
                Id = sp.Id,
                SellerId = sp.SellerId,
                ProductId = sp.ProductId,
                ExternalName = sp.ExternalName,
                ExternalUrl = sp.ExternalUrl,
                IsMatched = sp.IsMatched,
                MatchConfidence = sp.MatchConfidence,
                IsActive = sp.IsActive,
                LastCollectedAt = sp.LastCollectedAt
            })
            .ToListAsync();
    }

    public async Task<SellerProductDto> CreateAsync(CreateSellerProductDto dto)
    {
        var entity = new SellerProduct
        {
            SellerId = dto.SellerId,
            ExternalName = dto.ExternalName,
            ExternalUrl = dto.ExternalUrl,
            ExternalId = dto.ExternalId,
            ProductId = dto.ProductId,
            IsMatched = dto.ProductId is not null,
            MatchConfidence = dto.ProductId is not null ? 100m : null // elle girildiği için tam güven
        };

        await _sellerProductRepo.AddAsync(entity);
        await _sellerProductRepo.SaveChangesAsync();

        return new SellerProductDto
        {
            Id = entity.Id,
            SellerId = entity.SellerId,
            ProductId = entity.ProductId,
            ExternalName = entity.ExternalName,
            ExternalUrl = entity.ExternalUrl,
            IsMatched = entity.IsMatched,
            MatchConfidence = entity.MatchConfidence,
            IsActive = entity.IsActive
        };
    }

    public async Task UpdateMatchAsync(int id, UpdateMatchDto dto)
    {
        var sellerProduct = await _sellerProductRepo.GetByIdAsync(id)
            ?? throw new NotFoundException($"SellerProduct bulunamadı: {id}");

        var product = await _productRepo.GetByIdAsync(dto.ProductId)
            ?? throw new NotFoundException($"Ürün bulunamadı: {dto.ProductId}");

        sellerProduct.ProductId = product.Id;
        sellerProduct.IsMatched = true;
        sellerProduct.MatchConfidence = 100m; // manuel eşleştirme = tam güven

        _sellerProductRepo.Update(sellerProduct);
        await _sellerProductRepo.SaveChangesAsync();
    }

    public async Task<List<AutoMatchResultDto>> AutoMatchAsync(decimal thresholdPercent = 80)
    {
        var unmatched = await _sellerProductRepo.GetQueryable()
            .Where(sp => !sp.IsMatched && sp.IsActive)
            .ToListAsync();

        var products = await _productRepo.GetQueryable()
            .Where(p => p.IsActive)
            .ToListAsync();

        var results = new List<AutoMatchResultDto>();

        foreach (var sp in unmatched)
        {
            Product? best = null;
            decimal bestScore = 0;

            foreach (var product in products)
            {
                var score = NameNormalizer.CalculateSimilarity(sp.ExternalName, product.Name);
                if (score > bestScore)
                {
                    bestScore = score;
                    best = product;
                }
            }

            var applied = best is not null && bestScore >= thresholdPercent;

            if (applied)
            {
                sp.ProductId = best!.Id;
                sp.IsMatched = true;
                sp.MatchConfidence = bestScore;
                _sellerProductRepo.Update(sp);
            }

            results.Add(new AutoMatchResultDto
            {
                SellerProductId = sp.Id,
                ExternalName = sp.ExternalName,
                MatchedProductId = best?.Id,
                MatchedProductName = best?.Name,
                Confidence = bestScore,
                Applied = applied
            });
        }

        await _sellerProductRepo.SaveChangesAsync();
        return results;
    }

}
