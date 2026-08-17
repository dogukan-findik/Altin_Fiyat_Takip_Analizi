

namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class PriceHistoryStatsDto
{
    public int TotalRecords { get; set; }
    public int TotalProductsTracked { get; set; }
    public int TotalSellersActive { get; set; }
    public DateTime? OldestRecord { get; set; }
    public DateTime? NewestRecord { get; set; }
}
