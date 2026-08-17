

namespace Altin_Fiyat_Takip_Analizi.Application.DTOs;

public class PriceHistoryFilterDto
{
    public int? ProductId { get; set; }
    public int? SellerId { get; set; }
    public DateTime? From { get; set; }
    public DateTime? To { get; set; }
}
