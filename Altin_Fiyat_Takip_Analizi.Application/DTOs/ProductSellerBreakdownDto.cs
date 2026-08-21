namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class ProductSellerBreakdownDto
{
    public int ProductId { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public decimal OurPrice { get; set; }
    public List<SellerPriceEntryDto> SellerPrices { get; set; } = new();
}