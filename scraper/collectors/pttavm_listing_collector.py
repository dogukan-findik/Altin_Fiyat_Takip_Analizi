import time
from playwright.sync_api import sync_playwright
from scraper.collectors.base_collector import BaseCollector
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)


class PttavmListingCollector(BaseCollector):
    """PTTAVM kampanya sayfalarındaki (ör. /kampanyalar/en-fiyat-altin) ürünleri
    Playwright ve React router hydration state'i üzerinden eksiksiz çeker.
    
    Sayfa içi JSON hydration datasında her ürünün ID, başlık, indirimli/normal fiyat,
    ürün linki ve doğrudan MAĞAZA (shop.shop_name) bilgisi yer alır.
    Böylece ek detay sayfasına gitmeye gerek kalmaz."""

    def __init__(self, seller_config: dict):
        self.seller_config = seller_config
        self.base_url = seller_config["base_url"]
        self.selectors = seller_config.get("selectors", {})
        self.exclude_terms = [t.lower() for t in seller_config.get("exclude_brand_contains", [])]
        self.exclude_title_terms = [t.lower() for t in seller_config.get("exclude_title_contains", [])]
        self.max_pages = seller_config.get("max_pages", None)  # None = tüm sayfalar
        self.page_delay = seller_config.get("page_delay_seconds", 1.5)

    @retry(max_attempts=3, base_delay_seconds=3.0)
    def collect(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        page_idx = 1

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )
            while True:
                if self.max_pages and page_idx > self.max_pages:
                    logger.info("PTTAVM: Max sayfa limitine ulaşıldı (%d), durduruluyor.", self.max_pages)
                    break

                page_url = f"{self.base_url}?page={page_idx}" if page_idx > 1 else self.base_url
                logger.info("PTTAVM sayfa %d çekiliyor: %s", page_idx, page_url)
                
                page = context.new_page()
                try:
                    page.goto(page_url, wait_until="domcontentloaded", timeout=SCRAPE_TIMEOUT * 1000)
                    time.sleep(2)

                    hydration_data = page.evaluate("() => window.__staticRouterHydrationData")
                    if not hydration_data:
                        time.sleep(2)
                        hydration_data = page.evaluate("() => window.__staticRouterHydrationData")

                    if not hydration_data:
                        logger.warning("PTTAVM sayfa %d: __staticRouterHydrationData bulunamadı.", page_idx)
                        page.close()
                        break

                    loader_data = hydration_data.get("loaderData", {})
                    products = []
                    for lk, lv in loader_data.items():
                        if isinstance(lv, dict):
                            queries = lv.get("dehydratedState", {}).get("queries", [])
                            for q in queries:
                                if any("campaignInternal" in str(x) for x in q.get("queryKey", [])):
                                    products = q.get("state", {}).get("data", {}).get("products", [])
                                    if products:
                                        break
                        if products:
                            break

                    if not products:
                        logger.info("PTTAVM sayfa %d: Ürün bulunamadı, pagination bitti.", page_idx)
                        page.close()
                        break

                    logger.info("PTTAVM sayfa %d: %d ürün bulundu.", page_idx, len(products))

                    for prod in products:
                        name = prod.get("name", "").strip()
                        if not name:
                            continue

                        # Başlık filtresi (ör. çoklu adet paketleri)
                        lower_name = name.lower()
                        if any(t in lower_name for t in self.exclude_title_terms):
                            continue

                        # Satıcı bilgisi
                        shop = prod.get("shop", {})
                        shop_name = shop.get("shop_name", "").strip() if shop else "PTTAVM Satıcısı"
                        if not shop_name:
                            shop_name = "PTTAVM Satıcısı"

                        # Kendi satıcımız kontrolü (Ahlatcı)
                        lower_shop = shop_name.lower().replace(" ", "")
                        if any(term.replace(" ", "") in lower_shop for term in self.exclude_terms):
                            logger.debug("PTTAVM: Kendi mağazamız atlandı: %s (%s)", name, shop_name)
                            continue

                        # Fiyat belirleme: discountedPrice -> regularPrice -> originalPrice
                        price_info = prod.get("priceInfo", {})
                        price_val = (
                            price_info.get("discountedPrice")
                            or price_info.get("regularPrice")
                            or price_info.get("originalPrice")
                        )
                        if not price_val:
                            raw_price_text = prod.get("original_price", "")
                        else:
                            raw_price_text = f"{price_val:.2f}"

                        # Ürün linki
                        prod_url = prod.get("url", "")
                        if prod_url and not prod_url.startswith("http"):
                            prod_url = "https://www.pttavm.com" + prod_url
                        if not prod_url:
                            prod_url = f"https://www.pttavm.com/item/{prod.get('id')}"

                        items.append(
                            ScrapedItem(
                                external_name=name,
                                external_url=prod_url,
                                external_id=str(prod.get("id")),
                                raw_price=str(raw_price_text),
                                raw_availability=None,
                                seller_name=shop_name,
                            )
                        )

                    page.close()
                    page_idx += 1
                    time.sleep(self.page_delay)

                except Exception as exc:
                    logger.error("PTTAVM sayfa %d çekilirken hata: %s", page_idx, exc)
                    try:
                        page.close()
                    except Exception:
                        pass
                    break

            browser.close()

        logger.info("PttavmListingCollector: TOPLAM %d ürün toplandı (%s)", len(items), self.base_url)
        return items
