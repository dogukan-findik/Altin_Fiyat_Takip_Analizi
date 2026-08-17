using Microsoft.AspNetCore.Mvc;

namespace Altin_Fiyat_Takip_Analizi.API.Middleware
{
    public class RequestTimingController : Controller
    {
        public IActionResult Index()
        {
            return View();
        }
    }
}
