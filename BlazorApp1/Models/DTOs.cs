namespace Altin_Fiyat_Takip_Analizi.Web.Models;

public class LoginDto
{
    public string Username { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
}

public class AuthResponseDto
{
    public string Token { get; set; } = string.Empty;
    public string Username { get; set; } = string.Empty;
    public string Role { get; set; } = string.Empty;
    public DateTime ExpiresAt { get; set; }
}

public class PriceComparisonDto
{
    public int ProductId { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public decimal OurPrice { get; set; }
    public decimal CompetitorAvgPrice { get; set; }
    public decimal MinPrice { get; set; }
    public string MinPriceSeller { get; set; } = string.Empty;
    public decimal MaxPrice { get; set; }
    public string MaxPriceSeller { get; set; } = string.Empty;
    public decimal DiffFromAvg { get; set; }
    public DateTime CalculatedAt { get; set; }
}

public class SellerPriceEntryDto
{
    public int SellerId { get; set; }
    public string SellerName { get; set; } = string.Empty;
    public decimal? Price { get; set; }
    public decimal? DiffFromOurs { get; set; }
}

public class ProductSellerBreakdownDto
{
    public int ProductId { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public decimal OurPrice { get; set; }
    public List<SellerPriceEntryDto> SellerPrices { get; set; } = new();
}