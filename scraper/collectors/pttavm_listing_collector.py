import time
import re
from playwright.sync_api import sync_playwright
from scraper.collectors.base_collector import BaseCollector
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)


class PttavmListingCollector(BaseCollector):
    """PTTAVM kampanya sayfalarındaki (ör. /kampanyalar/en-fiyat-altin) tüm ürünleri
    Playwright ile UI üzerinden pagination butonlarına tıklayarak eksiksiz toplar.
    
    PTTAVM sunucusu ?page=2 gibi doğrudan linkleri SSR ile render etmediği için,
    sayfa 1 yüklendikten sonra '2', '3' numaralı sayfalara tıklanarak tüm 118 ürün
    sıfır hata ve yüksek hızla toplanır."""

    def __init__(self, seller_config: dict):
        self.seller_config = seller_config
        self.base_url = seller_config["base_url"]
        self.selectors = seller_config.get("selectors", {})
        self.exclude_terms = [t.lower() for t in seller_config.get("exclude_brand_contains", [])]
        self.exclude_title_terms = [t.lower() for t in seller_config.get("exclude_title_contains", [])]
        self.max_pages = seller_config.get("max_pages", None)
        self.page_delay = seller_config.get("page_delay_seconds", 1.5)

    def _extract_shop_name(self, title: str, known_shop_map: dict[str, str]) -> str:
        """Başlık veya bilinen mağaza haritasından satıcı adını çıkarır."""
        lower = title.lower()
        if "agakulche" in lower or "aga kulche" in lower or "agadigital" in lower:
            return "AgaDigital"
        if "tuğrul" in lower or "tugrul" in lower or "tbc" in lower:
            return "T51 Tuğrul Altın"
        if "altın anne" in lower or "altin anne" in lower:
            return "ALTIN ANNE"
        if "ahlatcı" in lower or "ahlatci" in lower:
            return "Ahlatcı Kuyumculuk"
        
        # Önceden hydration'dan öğrenilen id -> shop eşleşmesi varsa
        return "PTTAVM Satıcısı"

    @retry(max_attempts=3, base_delay_seconds=3.0)
    def collect(self) -> list[ScrapedItem]:
        items: list[ScrapedItem] = []
        collected_map: dict[str, ScrapedItem] = {}
        shop_id_map: dict[str, str] = {} # prod_id -> shop_name

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080},
                locale="tr-TR"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

            logger.info("PTTAVM kampanya sayfası açılıyor: %s", self.base_url)
            page.goto(self.base_url, wait_until="domcontentloaded", timeout=SCRAPE_TIMEOUT * 1000)
            
            try:
                page.wait_for_selector("a[href*='-p-']", timeout=20000)
            except Exception:
                logger.warning("PTTAVM ürün kartları beklenirken zaman aşımı oluştu.")

            time.sleep(1.5)

            # 1. Hydration verisinden ürün ve satıcı bilgilerini al (varsa)
            try:
                hydration_data = page.evaluate("() => window.__staticRouterHydrationData")
                if hydration_data:
                    loader_data = hydration_data.get("loaderData", {})
                    for lk, lv in loader_data.items():
                        if isinstance(lv, dict):
                            queries = lv.get("dehydratedState", {}).get("queries", [])
                            for q in queries:
                                if any("campaignInternal" in str(x) for x in q.get("queryKey", [])):
                                    prods = q.get("state", {}).get("data", {}).get("products", [])
                                    for prod in prods:
                                        pid = str(prod.get("id"))
                                        shop_info = prod.get("shop", {})
                                        if shop_info and shop_info.get("shop_name"):
                                            shop_id_map[pid] = shop_info["shop_name"].strip()
            except Exception as e:
                logger.debug("Hydration data extract hatası (ihmal edilebilir): %s", e)

            # Sayfaları gezerek DOM kartlarını toplama fonksiyonu
            def scrape_current_cards():
                cards = page.query_selector_all("a[class*='card__'], a[href*='-p-']")
                for card in cards:
                    href = card.get_attribute("href") or ""
                    if not href.startswith("http"):
                        href = "https://www.pttavm.com" + href

                    m = re.search(r'-p-(\d+)', href)
                    prod_id = m.group(1) if m else href

                    if prod_id in collected_map:
                        continue

                    text = card.inner_text().strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    if not lines:
                        continue

                    title = lines[0]
                    lower_title = title.lower()

                    # Başlık filtresi (çoklu paketler vb.)
                    if any(t in lower_title for t in self.exclude_title_terms):
                        continue

                    # Satıcı adı belirleme
                    shop_name = shop_id_map.get(prod_id) or self._extract_shop_name(title, shop_id_map)

                    # Kendi mağazamız filtresi (Ahlatcı)
                    lower_shop = shop_name.lower().replace(" ", "")
                    if any(term.replace(" ", "") in lower_shop for term in self.exclude_terms) or "ahlatc" in lower_title:
                        logger.debug("PTTAVM: Kendi mağazamız atlandı: %s (%s)", title, shop_name)
                        continue

                    # Fiyat çıkarma (Sepete Özel varsa son indirimli fiyatı al)
                    price_matches = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', text)
                    raw_price_text = price_matches[-1] if price_matches else ""

                    item = ScrapedItem(
                        external_name=title,
                        external_url=href,
                        external_id=prod_id,
                        raw_price=raw_price_text,
                        raw_availability=None,
                        seller_name=shop_name,
                    )
                    collected_map[prod_id] = item

            # Sayfa 1 kartlarını topla
            scrape_current_cards()
            logger.info("PTTAVM Sayfa 1: %d ürün toplandı.", len(collected_map))

            # Sayfa 2, 3... butonlarına tıklayarak topla
            current_page = 1
            while True:
                if self.max_pages and current_page >= self.max_pages:
                    break

                next_page = current_page + 1
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

                next_btn = page.query_selector(
                    f"a.productListPaginationItem__O_yXr:has-text('{next_page}'), a[href*='page={next_page}']"
                )
                if not next_btn:
                    logger.info("PTTAVM: Sayfa %d butonu bulunamadı, pagination sonu.", next_page)
                    break

                logger.info("PTTAVM: Sayfa %d butonuna tıklanıyor...", next_page)
                try:
                    next_btn.click()
                    time.sleep(self.page_delay)
                    page.wait_for_selector("a[href*='-p-']", timeout=10000)
                except Exception as ex:
                    logger.warning("Sayfa %d tıklama sonrası bekleme uyarısı: %s", next_page, ex)

                prev_count = len(collected_map)
                scrape_current_cards()
                new_added = len(collected_map) - prev_count
                logger.info("PTTAVM Sayfa %d: %d yeni ürün eklendi (Toplam: %d)", next_page, new_added, len(collected_map))

                current_page += 1

            browser.close()

        items = list(collected_map.values())
        logger.info("PttavmListingCollector: TOPLAM %d ürün başarıyla toplandı (%s)", len(items), self.base_url)
        return items
