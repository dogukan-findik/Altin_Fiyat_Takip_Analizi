using Altin_Fiyat_Takip_Analizi.Domain.Enums;

namespace Altin_Fiyat_Takip_Analizi.Domain.Entities;

public class CollectionJob
{
    public int Id { get; set; }
    public string JobType { get; set; } = string.Empty; // Manual, Scheduled, Test
    public JobStatus Status { get; set; }
    public DateTime StartedAt { get; set; } = DateTime.UtcNow;
    public DateTime? CompletedAt { get; set; }
    public int ItemsProcessed { get; set; }
    public int ItemsSuccess { get; set; }
    public int ItemsFailed { get; set; }
    public string? ErrorMessage { get; set; }
    public string? TriggeredBy { get; set; } // "System", "User:admin"
}