using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using System.Reflection;

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Product> Products => Set<Product>();
    public DbSet<Seller> Sellers => Set<Seller>();
    public DbSet<SellerProduct> SellerProducts => Set<SellerProduct>();
    public DbSet<PriceHistory> PriceHistories => Set<PriceHistory>();
    public DbSet<CollectionJob> CollectionJobs => Set<CollectionJob>();
    public DbSet<DailyReport> DailyReports => Set<DailyReport>();
    public DbSet<PriceAlert> PriceAlerts => Set<PriceAlert>();
    public DbSet<User> Users => Set<User>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(Assembly.GetExecutingAssembly());
        base.OnModelCreating(modelBuilder);
    }
}