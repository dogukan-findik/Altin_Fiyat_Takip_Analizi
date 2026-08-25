namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class DailyReportDto
{
    public DateOnly ReportDate { get; set; }
    public List<PriceComparisonDto> Comparisons { get; set; } = new();
    public int TotalProductsTracked { get; set; }
    public int TotalSellersActive { get; set; }

    // Günlük rapor özet istatistikleri
    public int ProductsBelowAvg { get; set; }       // Rakip ortalamasından ucuz ürün sayısı
    public int ProductsAboveAvg { get; set; }       // Rakip ortalamasından pahalı ürün sayısı
    public decimal AvgPriceDiffPercent { get; set; } // Ortalama fiyat farkı yüzdesi
    public string? CheapestProductName { get; set; } // En ucuz olan ürünümüz (rakibe göre)
    public decimal CheapestProductDiffPercent { get; set; }
    public string? MostExpensiveProductName { get; set; } // En pahalı olan ürünümüz (rakibe göre)
    public decimal MostExpensiveProductDiffPercent { get; set; }
    public int TotalPriceCollections { get; set; }   // Gün içinde yapılan toplam fiyat toplama sayısı
    public DateTime GeneratedAt { get; set; }
}
