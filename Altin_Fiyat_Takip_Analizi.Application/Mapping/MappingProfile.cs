using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;

using AutoMapper;

namespace Altin_Fiyat_Takip_Analizi.Application.Mapping;

public class MappingProfile : Profile
{
    public MappingProfile()
    {
        CreateMap<Product, ProductDto>();
        CreateMap<CreateProductDto, Product>();

        CreateMap<Seller, SellerDto>();

        CreateMap<PriceHistory, PriceHistoryDto>();
    }
}