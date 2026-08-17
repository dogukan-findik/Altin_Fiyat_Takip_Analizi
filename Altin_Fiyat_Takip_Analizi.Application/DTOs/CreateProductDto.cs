namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

// Yeni ürün eklerken kullanılır — Id ve CreatedAt gibi sunucu tarafında
// üretilen alanlar burada yok, DTO/Entity ayrımı bu yüzden gerekli.
public class CreateProductDto
{
    public string Name { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public decimal OurPrice { get; set; }
    public string Currency { get; set; } = "TRY";
}