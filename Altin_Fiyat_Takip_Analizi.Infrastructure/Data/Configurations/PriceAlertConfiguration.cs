using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Data.Configurations
{
    public class PriceAlertConfiguration : IEntityTypeConfiguration<PriceAlert>
    {
        public void Configure(EntityTypeBuilder<PriceAlert> builder)
        {
            builder.ToTable("PriceAlerts");
            builder.HasKey(pa => pa.Id);
            builder.Property(pa => pa.ThresholdType).HasMaxLength(20).IsRequired();
            builder.Property(pa => pa.ThresholdValue).HasColumnType("decimal(18,2)");
            builder.Property(pa => pa.CreatedAt).HasDefaultValueSql("GETUTCDATE()");

            builder.HasOne(pa => pa.Product).WithMany().HasForeignKey(pa => pa.ProductId);
        }
    }
}
