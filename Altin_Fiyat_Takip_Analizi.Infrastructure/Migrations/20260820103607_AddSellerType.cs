using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddSellerType : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "Type",
                table: "Sellers",
                type: "nvarchar(20)",
                maxLength: 20,
                nullable: false,
                defaultValue: "Bank");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Type",
                table: "Sellers");
        }
    }
}
