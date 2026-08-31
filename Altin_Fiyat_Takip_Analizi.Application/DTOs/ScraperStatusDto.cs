namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class ScraperStatusDto
{
    public string Platform { get; set; } = string.Empty;
    public bool IsScraping { get; set; }
    public DateTime? LastScrapedAt { get; set; }
}
