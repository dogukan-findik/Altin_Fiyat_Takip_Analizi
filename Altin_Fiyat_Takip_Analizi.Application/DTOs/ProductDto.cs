namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class ProductDto
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public decimal OurPrice { get; set; }
    public string Currency { get; set; } = "TRY";
    public bool IsActive { get; set; }
}