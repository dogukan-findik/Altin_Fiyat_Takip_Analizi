
using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Altin_Fiyat_Takip_Analizi.Application.Exceptions;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using AutoMapper;
using Altin_Fiyat_Takip_Analizi.Application.Common;

namespace Altin_Fiyat_Takip_Analizi.Application.Services;

public class ProductService : IProductService
{
    private readonly IRepository<Product> _productRepo;
    private readonly IMapper _mapper;

    public ProductService(IRepository<Product> productRepo, IMapper mapper)
    {
        _productRepo = productRepo;
        _mapper = mapper;
    }

    public async Task<List<ProductDto>> GetAllAsync()
    {
        var products = await _productRepo.GetAllAsync();
        return _mapper.Map<List<ProductDto>>(products);
    }

    public async Task<ProductDto?> GetByIdAsync(int id)
    {
        var product = await _productRepo.GetByIdAsync(id);
        return product is null ? null : _mapper.Map<ProductDto>(product);
    }

    public async Task<ProductDto> CreateAsync(CreateProductDto dto)
    {
        var product = _mapper.Map<Product>(dto);
        product.NormalizedName = NameNormalizer.Normalize(dto.Name);

        await _productRepo.AddAsync(product);
        await _productRepo.SaveChangesAsync();

        return _mapper.Map<ProductDto>(product);
    }

    public async Task UpdateAsync(int id, CreateProductDto dto)
    {
        var product = await _productRepo.GetByIdAsync(id)
            ?? throw new NotFoundException($"Ürün bulunamadı: {id}");

        product.Name = dto.Name;
        product.NormalizedName = NameNormalizer.Normalize(dto.Name);
        product.Category = dto.Category;
        product.OurPrice = dto.OurPrice;
        product.Currency = dto.Currency;

        _productRepo.Update(product);
        await _productRepo.SaveChangesAsync();
    }

    public async Task DeleteAsync(int id)
    {
        var product = await _productRepo.GetByIdAsync(id)
            ?? throw new NotFoundException($"Ürün bulunamadı: {id}");

        _productRepo.Remove(product);
        await _productRepo.SaveChangesAsync();
    }

   
}