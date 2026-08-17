using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Data.Configurations
{
    
    public class PriceHistoryConfiguration : IEntityTypeConfiguration<PriceHistory>
    {
        public void Configure(EntityTypeBuilder<PriceHistory> builder)
        {
            builder.ToTable("PriceHistory");
            builder.HasKey(ph => ph.Id);
            builder.Property(ph => ph.Price).HasColumnType("decimal(18,2)").IsRequired();
            builder.Property(ph => ph.Currency).HasMaxLength(3).HasDefaultValue("TRY");
            builder.Property(ph => ph.CollectedAt).HasDefaultValueSql("GETUTCDATE()");

            builder.HasIndex(ph => ph.SellerProductId).HasDatabaseName("IX_PriceHistory_SellerProductId");
            builder.HasIndex(ph => ph.CollectedAt).HasDatabaseName("IX_PriceHistory_CollectedAt");

            // Fiyat geçmişi korunmalı — SellerProduct silinse bile PriceHistory silinmez
            builder.HasOne(ph => ph.SellerProduct)
                .WithMany(sp => sp.PriceHistories)
                .HasForeignKey(ph => ph.SellerProductId)
                .OnDelete(DeleteBehavior.Restrict);
        }
    }
}
