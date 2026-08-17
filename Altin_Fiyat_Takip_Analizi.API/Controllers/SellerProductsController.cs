using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;

namespace Altin_Fiyat_Takip_Analizi.API.Controllers;
[ApiController]
[Route("api/v1/seller-products")]
[Authorize]

public class SellerProductsController : Controller
{
    private readonly ISellerProductService _service;

    public SellerProductsController(ISellerProductService service)
    {
        _service = service;
    }
   
    [HttpGet]
    public async Task<ActionResult<List<SellerProductDto>>> GetAll()
        => Ok(await _service.GetAllAsync());

    [HttpPost]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<SellerProductDto>> Create(CreateSellerProductDto dto)
        => Ok(await _service.CreateAsync(dto));

    [HttpPut("{id:int}/match")]
    [Authorize(Roles = "Admin")]
    public async Task<IActionResult> UpdateMatch(int id, UpdateMatchDto dto)
    {
        await _service.UpdateMatchAsync(id, dto);
        return NoContent();
    }

    [HttpPost("auto-match")]
    [Authorize(Roles = "Admin")]
    public async Task<ActionResult<List<AutoMatchResultDto>>> AutoMatch([FromQuery] decimal threshold = 80)
        => Ok(await _service.AutoMatchAsync(threshold));

}
