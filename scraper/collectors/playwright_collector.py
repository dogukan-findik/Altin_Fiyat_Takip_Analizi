from playwright.sync_api import sync_playwright
from scraper.collectors.base_collector import BaseCollector
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

class PlaywrightCollector(BaseCollector):
    """JavaScript ile render edilen dinamik siteler için."""

    @retry(max_attempts=3, base_delay_seconds=3.0)
    def collect(self) -> list[ScrapedItem]:
        items = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(self.base_url, timeout=SCRAPE_TIMEOUT * 1000)
            page.wait_for_selector(self.selectors["product_list"], timeout=SCRAPE_TIMEOUT * 1000)

            elements = page.query_selector_all(self.selectors["product_list"])
            for el in elements:
                name_el = el.query_selector(self.selectors["name"])
                price_el = el.query_selector(self.selectors["price"])
                link_el = el.query_selector(self.selectors.get("link", "a"))
                avail_el = el.query_selector(self.selectors.get("availability", ""))

                if not name_el or not price_el:
                    continue

                items.append(ScrapedItem(
                    external_name=name_el.inner_text().strip(),
                    external_url=link_el.get_attribute("href") if link_el else self.base_url,
                    external_id=link_el.get_attribute("href") if link_el else None,
                    raw_price=price_el.inner_text().strip(),
                    raw_availability=avail_el.inner_text().strip() if avail_el else None,
                ))

            browser.close()

        logger.info("PlaywrightCollector: %d ürün bulundu (%s)", len(items), self.base_url)
        return items
