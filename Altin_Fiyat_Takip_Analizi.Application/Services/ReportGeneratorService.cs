using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace Altin_Fiyat_Takip_Analizi.Application.Services;

public class ReportGeneratorService : IReportService
{
    private readonly IPriceComparisonService _comparisonService;
    private readonly IRepository<Seller> _sellerRepo;
    private readonly IRepository<DailyReport> _reportRepo;
    private readonly IRepository<Product> _productRepo;
    private readonly IRepository<CollectionJob> _jobRepo;

    public ReportGeneratorService(
        IPriceComparisonService comparisonService,
        IRepository<Seller> sellerRepo,
        IRepository<DailyReport> reportRepo,
        IRepository<Product> productRepo,
        IRepository<CollectionJob> jobRepo)
    {
        _comparisonService = comparisonService;
        _sellerRepo = sellerRepo;
        _reportRepo = reportRepo;
        _productRepo = productRepo;
        _jobRepo = jobRepo;
    }

    public async Task<DailyReportDto> GenerateDailyReportAsync(DateOnly date)
    {
        var comparisons = await _comparisonService.GetAllComparisonsAsync();
        var activeSellers = (await _sellerRepo.GetAllAsync()).Count(s => s.IsActive);

        // Gün içinde yapılan fiyat toplama job sayısı
        var dayStart = date.ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc);
        var dayEnd = date.AddDays(1).ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc);
        var totalCollections = await _jobRepo.GetQueryable()
            .CountAsync(j => j.StartedAt >= dayStart && j.StartedAt < dayEnd);

        foreach (var c in comparisons)
        {
            await _reportRepo.AddAsync(new DailyReport
            {
                ReportDate = date,
                ProductId = c.ProductId,
                OurPrice = c.OurPrice,
                CompetitorAvgPrice = c.CompetitorAvgPrice,
                MinPrice = c.MinPrice,
                MaxPrice = c.MaxPrice,
                PriceDiffFromAvg = c.DiffFromAvg,
                GeneratedAt = DateTime.UtcNow
            });
        }
        await _reportRepo.SaveChangesAsync();

        return BuildReportDto(date, comparisons, activeSellers, totalCollections);
    }

    public async Task<DailyReportDto?> GetReportByDateAsync(DateOnly date)
    {
        var reports = (await _reportRepo.GetAllAsync())
            .Where(r => r.ReportDate == date)
            .ToList();

        if (!reports.Any()) return null;

        // Rapor kapsamındaki ürünleri tek seferde çekip sözlükte tut (N+1 sorgu olmasın)
        var productIds = reports.Select(r => r.ProductId).Distinct().ToList();
        var products = await _productRepo.GetQueryable()
            .Where(p => productIds.Contains(p.Id))
            .ToDictionaryAsync(p => p.Id, p => p.Name);

        var comparisons = reports.Select(r => new PriceComparisonDto
        {
            ProductId = r.ProductId,
            ProductName = products.TryGetValue(r.ProductId, out var name) ? name : string.Empty,
            OurPrice = r.OurPrice ?? 0,
            CompetitorAvgPrice = r.CompetitorAvgPrice ?? 0,
            MinPrice = r.MinPrice ?? 0,
            MaxPrice = r.MaxPrice ?? 0,
            DiffFromAvg = r.PriceDiffFromAvg ?? 0,
            CalculatedAt = r.GeneratedAt
        }).ToList();

        var activeSellers = (await _sellerRepo.GetAllAsync()).Count(s => s.IsActive);

        // Gün içinde yapılan fiyat toplama job sayısı
        var dayStart = date.ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc);
        var dayEnd = date.AddDays(1).ToDateTime(TimeOnly.MinValue, DateTimeKind.Utc);
        var totalCollections = await _jobRepo.GetQueryable()
            .CountAsync(j => j.StartedAt >= dayStart && j.StartedAt < dayEnd);

        return BuildReportDto(date, comparisons, activeSellers, totalCollections);
    }
    public async Task<List<DailyReportDto>> GetWeeklySummaryAsync(DateOnly weekEndDate)
    {
        var summary = new List<DailyReportDto>();

        for (int i = 6; i >= 0; i--)
        {
            var date = weekEndDate.AddDays(-i);
            var report = await GetReportByDateAsync(date);
            if (report is not null)
                summary.Add(report);
        }

        return summary;
    }

    /// <summary>
    /// Karşılaştırma verilerinden özet istatistiklerle dolu bir DailyReportDto üretir.
    /// </summary>
    private static DailyReportDto BuildReportDto(
        DateOnly date,
        List<PriceComparisonDto> comparisons,
        int activeSellers,
        int totalCollections)
    {
        // Sadece rakip verisi olan ürünleri filtrele (CompetitorAvgPrice > 0)
        var withCompetitorData = comparisons
            .Where(c => c.CompetitorAvgPrice > 0 && c.OurPrice > 0)
            .ToList();

        // Fiyat farkı yüzdesi: (OurPrice - CompetitorAvg) / CompetitorAvg * 100
        var diffPercents = withCompetitorData
            .Select(c => new
            {
                c.ProductName,
                DiffPercent = c.CompetitorAvgPrice != 0
                    ? Math.Round((c.OurPrice - c.CompetitorAvgPrice) / c.CompetitorAvgPrice * 100, 2)
                    : 0m
            })
            .ToList();

        int belowAvg = diffPercents.Count(d => d.DiffPercent < 0);
        int aboveAvg = diffPercents.Count(d => d.DiffPercent > 0);
        decimal avgDiffPercent = diffPercents.Any()
            ? Math.Round(diffPercents.Average(d => d.DiffPercent), 2)
            : 0;

        var cheapest = diffPercents.MinBy(d => d.DiffPercent);
        var mostExpensive = diffPercents.MaxBy(d => d.DiffPercent);

        return new DailyReportDto
        {
            ReportDate = date,
            Comparisons = comparisons,
            TotalProductsTracked = comparisons.Count,
            TotalSellersActive = activeSellers,
            ProductsBelowAvg = belowAvg,
            ProductsAboveAvg = aboveAvg,
            AvgPriceDiffPercent = avgDiffPercent,
            CheapestProductName = cheapest?.ProductName,
            CheapestProductDiffPercent = cheapest?.DiffPercent ?? 0,
            MostExpensiveProductName = mostExpensive?.ProductName,
            MostExpensiveProductDiffPercent = mostExpensive?.DiffPercent ?? 0,
            TotalPriceCollections = totalCollections,
            GeneratedAt = DateTime.UtcNow
        };
    }
}