
using Altin_Fiyat_Takip_Analizi.Domain.Entities;

namespace Altin_Fiyat_Takip_Analizi.Application.Interfaces;

public interface IJwtService
{
    string GenerateToken(User user);
}