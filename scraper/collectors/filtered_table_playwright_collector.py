from playwright.sync_api import sync_playwright
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

class FilteredTablePlaywrightCollector:
    """FilteredTableCollector'ın JS ile render edilen siteler için
    Playwright tabanlı karşılığı — aynı filter_contains mantığı,
    farklı çekim yöntemi."""

    def __init__(self, seller_config: dict):
        self.base_url = seller_config["base_url"]
        self.selectors = seller_config["selectors"]
        self.filter_contains: str | None = seller_config.get("filter_contains")

    @retry(max_attempts=3, base_delay_seconds=3.0)
    def collect(self) -> list[ScrapedItem]:
        items = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(self.base_url, timeout=SCRAPE_TIMEOUT * 1000)

            # Tablo hücreleri sonradan JS ile dolduruluyor — statik
            # wait_for_selector yetmez, hücrenin GERÇEKTEN dolmasını
            # (boş olmayan metin) bekliyoruz.
            page.wait_for_function(
                """(sel) => {
                    const rows = document.querySelectorAll(sel);
                    return rows.length > 0 && [...rows].some(r => r.innerText.trim().length > 0);
                }""",
                arg=self.selectors["row"],
                timeout=SCRAPE_TIMEOUT * 1000
            )

            rows = page.query_selector_all(self.selectors["row"])
            for row in rows:
                name_el = row.query_selector(self.selectors["name"])
                price_el = row.query_selector(self.selectors["price"])

                if not name_el or not price_el:
                    continue
                
                name_text = name_el.inner_text().strip()
                if not name_text:
                    continue

                if self.filter_contains and self.filter_contains.upper() not in name_text.upper():
                    continue

                items.append(ScrapedItem(
                    external_name=name_text,
                    external_url=self.base_url,
                    external_id=name_text,
                    raw_price=price_el.inner_text().strip(),
                    raw_availability=None,
                ))

            browser.close()

        if not items:
            logger.warning("FilteredTablePlaywrightCollector: filtreye uyan satır bulunamadı. URL: %s", self.base_url)

        logger.info("FilteredTablePlaywrightCollector: %d ürün bulundu (%s)", len(items), self.base_url)
        return items
