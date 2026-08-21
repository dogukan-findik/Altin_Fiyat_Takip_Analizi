namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class SellerPriceEntryDto
{
    public int SellerId { get; set; }
    public string SellerName { get; set; } = string.Empty;
    public decimal? Price { get; set; }        // null = bu satıcıda bu ürün bulunamadı
    public decimal? DiffFromOurs { get; set; }
}