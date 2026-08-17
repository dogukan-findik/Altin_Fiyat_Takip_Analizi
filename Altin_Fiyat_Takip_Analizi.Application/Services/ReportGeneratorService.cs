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

    public ReportGeneratorService(
        IPriceComparisonService comparisonService,
        IRepository<Seller> sellerRepo,
        IRepository<DailyReport> reportRepo,
        IRepository<Product> productRepo)
    {
        _comparisonService = comparisonService;
        _sellerRepo = sellerRepo;
        _reportRepo = reportRepo;
        _productRepo = productRepo;
    }

    public async Task<DailyReportDto> GenerateDailyReportAsync(DateOnly date)
    {
        var comparisons = await _comparisonService.GetAllComparisonsAsync();
        var activeSellers = (await _sellerRepo.GetAllAsync()).Count(s => s.IsActive);

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

        return new DailyReportDto
        {
            ReportDate = date,
            Comparisons = comparisons,
            TotalProductsTracked = comparisons.Count,
            TotalSellersActive = activeSellers
        };
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

        return new DailyReportDto
        {
            ReportDate = date,
            Comparisons = comparisons,
            TotalProductsTracked = comparisons.Count
        };
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
}