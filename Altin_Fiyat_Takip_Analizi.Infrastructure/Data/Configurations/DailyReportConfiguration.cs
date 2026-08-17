using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Data.Configurations
{
    public class DailyReportConfiguration : IEntityTypeConfiguration<DailyReport>
    {
        public void Configure(EntityTypeBuilder<DailyReport> builder)
        {
            builder.ToTable("DailyReports");
            builder.HasKey(dr => dr.Id);
            builder.Property(dr => dr.OurPrice).HasColumnType("decimal(18,2)");
            builder.Property(dr => dr.CompetitorAvgPrice).HasColumnType("decimal(18,2)");
            builder.Property(dr => dr.MinPrice).HasColumnType("decimal(18,2)");
            builder.Property(dr => dr.MaxPrice).HasColumnType("decimal(18,2)");
            builder.Property(dr => dr.PriceDiffFromAvg).HasColumnType("decimal(18,2)");
            builder.Property(dr => dr.GeneratedAt).HasDefaultValueSql("GETUTCDATE()");

            builder.HasIndex(dr => dr.ReportDate).HasDatabaseName("IX_DailyReports_ReportDate");
            builder.HasIndex(dr => dr.ProductId).HasDatabaseName("IX_DailyReports_ProductId");

            builder.HasOne(dr => dr.Product).WithMany().HasForeignKey(dr => dr.ProductId);
            builder.HasOne(dr => dr.MinPriceSeller).WithMany()
                .HasForeignKey(dr => dr.MinPriceSellerId).OnDelete(DeleteBehavior.NoAction);
            builder.HasOne(dr => dr.MaxPriceSeller).WithMany()
                .HasForeignKey(dr => dr.MaxPriceSellerId).OnDelete(DeleteBehavior.NoAction);
        }
    }
}
