import requests
from bs4 import BeautifulSoup
from scraper.collectors.base_collector import BaseCollector
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

class RequestsCollector(BaseCollector):
    """Sunucu tarafında render edilen (JS gerektirmeyen) statik siteler için."""

    @retry(max_attempts=3, base_delay_seconds=2.0)
    def _fetch(self) -> str:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(self.base_url, headers=headers, timeout=SCRAPE_TIMEOUT)
        response.raise_for_status()
        return response.text

    def collect(self) -> list[ScrapedItem]:
        html = self._fetch()
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for el in soup.select(self.selectors["product_list"]):
            name_el = el.select_one(self.selectors["name"])
            price_el = el.select_one(self.selectors["price"])
            link_el = el.select_one(self.selectors.get("link", "a"))
            avail_el = el.select_one(self.selectors.get("availability", ""))

            if not name_el or not price_el:
                continue

            items.append(ScrapedItem(
                external_name=name_el.get_text(strip=True),
                external_url=link_el.get("href", "") if link_el else self.base_url,
                external_id=link_el.get("href") if link_el else None,
                raw_price=price_el.get_text(strip=True),
                raw_availability=avail_el.get_text(strip=True) if avail_el else None,
            ))

        logger.info("RequestsCollector: %d ürün bulundu (%s)", len(items), self.base_url)
        return items
