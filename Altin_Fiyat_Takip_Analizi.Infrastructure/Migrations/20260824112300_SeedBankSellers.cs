using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class SeedBankSellers : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // Seed the 3 banks with explicit Bank type
            migrationBuilder.InsertData(
                table: "Sellers",
                columns: new[] { "Name", "WebsiteUrl", "Type", "IsActive", "CreatedAt", "UpdatedAt" },
                values: new object[,]
                {
                    { "Garanti BBVA", "https://www.garantibbva.com.tr", "Bank", true, DateTime.UtcNow, DateTime.UtcNow },
                    { "QNB Finansbank", "https://www.qnb.com.tr", "Bank", true, DateTime.UtcNow, DateTime.UtcNow },
                    { "Yapı Kredi", "https://www.yapikredi.com.tr", "Bank", true, DateTime.UtcNow, DateTime.UtcNow }
                });

            // Update any existing sellers that have n11.com URLs to Marketplace type
            migrationBuilder.Sql(
                "UPDATE Sellers SET Type = 'Marketplace', UpdatedAt = GETUTCDATE() " +
                "WHERE WebsiteUrl LIKE '%n11.com%' AND Type != 'Marketplace'");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            // Remove the seeded bank sellers
            migrationBuilder.DeleteData(
                table: "Sellers",
                keyColumn: "Name",
                keyValues: new object[] { "Garanti BBVA", "QNB Finansbank", "Yapı Kredi" });
        }
    }
}
