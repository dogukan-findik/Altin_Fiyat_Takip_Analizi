namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class SellerDto
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? WebsiteUrl { get; set; }
    public bool IsActive { get; set; }
}