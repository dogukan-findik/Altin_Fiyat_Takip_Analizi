using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Domain.Enums;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace Altin_Fiyat_Takip_Analizi.API.Controllers;
[ApiController]
[Route("api/v1/products")]
[Authorize]

public class ProductsController : ControllerBase
{
    private readonly IProductService _productService;
    private readonly IPriceHistoryService _historyService;
    private readonly IPriceComparisonService _comparisonService;

    public ProductsController(IProductService productService,
    IPriceHistoryService historyService,
    IPriceComparisonService comparisonService)
    {   _productService = productService;
        _historyService = historyService;
        _comparisonService = comparisonService;
    }

    [HttpGet]
    public async Task<ActionResult<List<ProductDto>>> GetAll()
        => Ok(await _productService.GetAllAsync());

    [HttpGet("{id:int}")]
    public async Task<ActionResult<ProductDto>> GetById(int id)
    {
        var product = await _productService.GetByIdAsync(id);
        return product is null ? NotFound() : Ok(product);
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<ProductDto>> Create(CreateProductDto dto)
    {
        var created = await _productService.CreateAsync(dto);
        return CreatedAtAction(nameof(GetById), new { id = created.Id }, created);
    }

    [HttpPut("{id:int}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Update(int id, CreateProductDto dto)
    {
        await _productService.UpdateAsync(id, dto);
        return NoContent();
    }

    [HttpDelete("{id:int}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Delete(int id)
    {
        await _productService.DeleteAsync(id);
        return NoContent();
    }

    [HttpGet("{id:int}/history")]
    public async Task<ActionResult<List<PriceHistoryDto>>> GetHistory(int id, [FromQuery] int days = 30)
        => Ok(await _historyService.GetForProductAsync(id, days));

    [HttpGet("{id:int}/compare")]
    public async Task<ActionResult<PriceComparisonDto>> Compare(int id, [FromQuery] SellerType? sellerType = null)
     => Ok(await _comparisonService.ComparePricesAsync(id, sellerType));

    [HttpGet("compare-all")]
    public async Task<ActionResult<List<PriceComparisonDto>>> CompareAll([FromQuery] SellerType? sellerType = null)
    => Ok(await _comparisonService.GetAllComparisonsAsync(sellerType));

    [HttpGet("seller-breakdown")]
    public async Task<ActionResult<List<ProductSellerBreakdownDto>>> SellerBreakdown([FromQuery] SellerType sellerType)
    => Ok(await _comparisonService.GetSellerBreakdownAsync(sellerType));

    [HttpGet("seller-product-breakdown")]
    public async Task<ActionResult<List<SellerProductBreakdownDto>>> SellerProductBreakdown(
        [FromQuery] SellerType sellerType,
        [FromQuery] string? platform = null)
        => Ok(await _comparisonService.GetSellerProductBreakdownAsync(sellerType, platform));

}

