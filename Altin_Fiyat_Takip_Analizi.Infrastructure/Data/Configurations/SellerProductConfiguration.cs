using  Microsoft.EntityFrameworkCore;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Data.Configurations
{
    public class SellerProductConfiguration : IEntityTypeConfiguration<SellerProduct>
    {
        public void Configure(EntityTypeBuilder<SellerProduct> builder)
        {
            builder.ToTable("SellerProducts");
            builder.HasKey(sp => sp.Id);
            builder.Property(sp => sp.ExternalName).HasMaxLength(300).IsRequired();
            builder.Property(sp => sp.ExternalUrl).HasMaxLength(1000).IsRequired();
            builder.Property(sp => sp.ExternalId).HasMaxLength(200);
            builder.Property(sp => sp.MatchConfidence).HasColumnType("decimal(5,2)");
            builder.Property(sp => sp.CreatedAt).HasDefaultValueSql("GETUTCDATE()");

            builder.HasIndex(sp => new { sp.SellerId, sp.ExternalId })
                .IsUnique()
                .HasDatabaseName("UQ_SellerProduct_External");

            builder.HasIndex(sp => sp.ProductId).HasDatabaseName("IX_SellerProducts_ProductId");
            builder.HasIndex(sp => sp.SellerId).HasDatabaseName("IX_SellerProducts_SellerId");

            builder.HasOne(sp => sp.Seller)
                .WithMany(s => s.SellerProducts)
                .HasForeignKey(sp => sp.SellerId)
                .OnDelete(DeleteBehavior.Cascade);

            builder.HasOne(sp => sp.Product)
                .WithMany(p => p.SellerProducts)
                .HasForeignKey(sp => sp.ProductId)
                .OnDelete(DeleteBehavior.SetNull);
        }
    }
}
