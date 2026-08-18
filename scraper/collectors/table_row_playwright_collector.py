from playwright.sync_api import sync_playwright
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

class TableRowPlaywrightCollector:
    """TableRowCollector'ın JS ile render edilen siteler için Playwright
    tabanlı karşılığı — aynı symbol_map mantığı, farklı çekim yöntemi."""

    def __init__(self, seller_config: dict):
        self.base_url = seller_config["base_url"]
        self.selectors = seller_config["selectors"]
        self.symbol_map: dict[str, str] = seller_config["symbol_map"]

    @retry(max_attempts=3, base_delay_seconds=3.0)
    def collect(self) -> list[ScrapedItem]:
        items = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(self.base_url, timeout=SCRAPE_TIMEOUT * 1000)
            page.wait_for_selector(self.selectors["row"], timeout=SCRAPE_TIMEOUT * 1000)

            rows = page.query_selector_all(self.selectors["row"])
            for row in rows:
                data_id = row.get_attribute("data-id")
                if not data_id or data_id not in self.symbol_map:
                    continue

                ask_el = row.query_selector(self.selectors["ask"])
                if not ask_el:
                    continue

                items.append(ScrapedItem(
                    external_name=self.symbol_map[data_id],
                    external_url=self.base_url,
                    external_id=data_id,
                    raw_price=ask_el.inner_text().strip(),
                    raw_availability=None,
                ))

            browser.close()

        if not items:
            logger.warning(
                "TableRowPlaywrightCollector: hiç satır bulunamadı, selector'ları "
                "tekrar kontrol et. URL: %s", self.base_url
            )

        logger.info("TableRowPlaywrightCollector: %d ürün bulundu (%s)", len(items), self.base_url)
        return items