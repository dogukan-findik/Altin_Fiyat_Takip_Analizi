using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using AutoMapper;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Altin_Fiyat_Takip_Analizi.Application.Exceptions;


namespace Altin_Fiyat_Takip_Analizi.Application.Services;

public class SellerService : ISellerService
{
    private readonly IMapper _mapper;
    private readonly IRepository<Seller> _sellerRepo;
    private readonly IRepository<SellerProduct> _sellerProductRepo;

    public SellerService(IMapper mapper, IRepository<Seller> sellerRepo, IRepository<SellerProduct> sellerProductRepo)
    {
        _mapper = mapper;
        _sellerRepo = sellerRepo;
        _sellerProductRepo = sellerProductRepo;
    }
    public async Task<List<SellerDto>> GetAllAsync()
        => _mapper.Map<List<SellerDto>>(await _sellerRepo.GetAllAsync());

    public async Task<SellerDto?> GetByIdAsync(int id)
    {
        var seller = await _sellerRepo.GetByIdAsync(id);
        return seller is null ? null : _mapper.Map<SellerDto>(seller);
    }

    public async Task<SellerDto> CreateAsync(SellerDto dto)
    {
        var seller = new Seller
        {
            Name = dto.Name,
            WebsiteUrl = dto.WebsiteUrl,
            IsActive = dto.IsActive
        };

        await _sellerRepo.AddAsync(seller);
        await _sellerRepo.SaveChangesAsync();

        return _mapper.Map<SellerDto>(seller);
    }

    public async Task UpdateAsync(int id, SellerDto dto)
    {
        var seller = await _sellerRepo.GetByIdAsync(id)
            ?? throw new NotFoundException($"Satıcı bulunamadı: {id}");

        seller.Name = dto.Name;
        seller.WebsiteUrl = dto.WebsiteUrl;
        seller.IsActive = dto.IsActive;
        seller.UpdatedAt = DateTime.UtcNow;

        _sellerRepo.Update(seller);
        await _sellerRepo.SaveChangesAsync();
    }

    public async Task DeleteAsync(int id)
    {
        var seller = await _sellerRepo.GetByIdAsync(id)
            ?? throw new NotFoundException($"Satıcı bulunamadı: {id}");

        _sellerRepo.Remove(seller);
        await _sellerRepo.SaveChangesAsync();
    }

    public async Task<List<SellerProductDto>> GetSellerProductsAsync(int sellerId)
    {
        return await _sellerProductRepo.GetQueryable()
            .Where(sp => sp.SellerId == sellerId)
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

}

