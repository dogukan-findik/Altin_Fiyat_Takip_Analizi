using Microsoft.AspNetCore.Mvc;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Microsoft.AspNetCore.Authorization;

namespace Altin_Fiyat_Takip_Analizi.API.Controllers;
[ApiController]
[Route("api/v1/sellers")]
[Authorize]

public class SellersController : ControllerBase
{
    private readonly ISellerService _sellerService;
    public SellersController(ISellerService sellerService)
    {
        _sellerService = sellerService;
    }

    [HttpGet]
    public async Task<ActionResult<List<SellerDto>>> GetAll()
       => Ok(await _sellerService.GetAllAsync());

    [HttpGet("{id:int}")]
    public async Task<ActionResult<SellerDto>> GetById(int id)
    {
        var seller = await _sellerService.GetByIdAsync(id);
        return seller is null ? NotFound() : Ok(seller);
    }

    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<SellerDto>> Create(SellerDto dto)
    {
        var created = await _sellerService.CreateAsync(dto);
        return CreatedAtAction(nameof(GetById), new { id = created.Id }, created);
    }

    [HttpPut("{id:int}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Update(int id, SellerDto dto)
    {
        await _sellerService.UpdateAsync(id, dto);
        return NoContent();
    }

    [HttpDelete("{id:int}")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> Delete(int id)
    {
        await _sellerService.DeleteAsync(id);
        return NoContent();
    }

    [HttpGet("{id:int}/products")]
    public async Task<ActionResult<List<SellerProductDto>>> GetProducts(int id)
        => Ok(await _sellerService.GetSellerProductsAsync(id));


}

