using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Altin_Fiyat_Takip_Analizi.Application.DTOs;
using Altin_Fiyat_Takip_Analizi.Application.Interfaces;

namespace Altin_Fiyat_Takip_Analizi.API.Controllers;

[ApiController]
[Route("api/v1/price-history")]
[Authorize]
public class PriceHistoryController : ControllerBase
{
    private readonly IPriceHistoryService _historyService;

    public PriceHistoryController(IPriceHistoryService historyService)
    {
        _historyService = historyService;
    }

    [HttpGet]
    public async Task<ActionResult<List<PriceHistoryDto>>> GetFiltered([FromQuery] PriceHistoryFilterDto filter)
        => Ok(await _historyService.GetFilteredAsync(filter));

    [HttpGet("latest")]
    public async Task<ActionResult<List<PriceHistoryDto>>> GetLatest()
        => Ok(await _historyService.GetLatestAsync());

    [HttpGet("stats")]
    public async Task<ActionResult<PriceHistoryStatsDto>> GetStats()
        => Ok(await _historyService.GetStatsAsync());
}