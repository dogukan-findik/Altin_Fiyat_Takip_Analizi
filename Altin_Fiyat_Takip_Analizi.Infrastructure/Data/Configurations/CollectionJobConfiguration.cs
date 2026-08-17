using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Altin_Fiyat_Takip_Analizi.Domain.Entities;

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Data.Configurations
{
    public class CollectionJobConfiguration : IEntityTypeConfiguration<CollectionJob>
    {
        public void Configure(EntityTypeBuilder<CollectionJob> builder)
        {
            builder.ToTable("CollectionJobs");
            builder.HasKey(cj => cj.Id);
            builder.Property(cj => cj.JobType).HasMaxLength(50).IsRequired();
            builder.Property(cj => cj.Status).HasConversion<string>().HasMaxLength(20);
            builder.Property(cj => cj.StartedAt).HasDefaultValueSql("GETUTCDATE()");
            builder.Property(cj => cj.TriggeredBy).HasMaxLength(100);
        }
     }
}
