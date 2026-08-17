namespace Altin_Fiyat_Takip_Analizi.Domain.Entities;

public class PriceAlert
{
    public int Id { get; set; }
    public int ProductId { get; set; }
    public string ThresholdType { get; set; } = string.Empty; // Below, Above, PercentChange
    public decimal ThresholdValue { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Product Product { get; set; } = null!;
}