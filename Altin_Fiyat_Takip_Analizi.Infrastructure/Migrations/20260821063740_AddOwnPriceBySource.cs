using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Altin_Fiyat_Takip_Analizi.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddOwnPriceBySource : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "OwnPriceBySource",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    ProductId = table.Column<int>(type: "int", nullable: false),
                    SourceType = table.Column<string>(type: "nvarchar(20)", maxLength: 20, nullable: false),
                    Price = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "datetime2", nullable: false, defaultValueSql: "GETUTCDATE()")
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_OwnPriceBySource", x => x.Id);
                    table.ForeignKey(
                        name: "FK_OwnPriceBySource_Products_ProductId",
                        column: x => x.ProductId,
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_OwnPriceBySource_ProductId_SourceType",
                table: "OwnPriceBySource",
                columns: new[] { "ProductId", "SourceType" },
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "OwnPriceBySource");
        }
    }
}
