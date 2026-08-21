using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Data.Configurations;

public class OwnPriceBySourceConfiguration : IEntityTypeConfiguration<OwnPriceBySource>
{
    public void Configure(EntityTypeBuilder<OwnPriceBySource> builder)
    {
        builder.ToTable("OwnPriceBySource");
        builder.HasKey(o => o.Id);
        builder.Property(o => o.SourceType).HasConversion<string>().HasMaxLength(20);
        builder.Property(o => o.Price).HasColumnType("decimal(18,2)");
        builder.Property(o => o.UpdatedAt).HasDefaultValueSql("GETUTCDATE()");

        builder.HasIndex(o => new { o.ProductId, o.SourceType }).IsUnique();

        builder.HasOne(o => o.Product)
            .WithMany()
            .HasForeignKey(o => o.ProductId)
            .OnDelete(DeleteBehavior.Cascade);
    }
}