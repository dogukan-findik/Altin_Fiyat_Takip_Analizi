import requests
from bs4 import BeautifulSoup
from scraper.collectors.base_collector import BaseCollector
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

class FilteredTableCollector(BaseCollector):
    """QNB gibi, tek bir tabloda hem döviz hem altın satırlarının karışık
    bulunduğu siteler için. 'name' metninde belirli bir alt string
    (örn. 'ALTIN') geçen satırlar alınır, geri kalanı (USD, EUR vb.) atlanır."""

    def __init__(self, seller_config: dict):
        super().__init__(seller_config)
        self.filter_contains: str | None = seller_config.get("filter_contains")

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

        for row in soup.select(self.selectors["row"]):
            name_el = row.select_one(self.selectors["name"])
            price_el = row.select_one(self.selectors["price"])

            if not name_el or not price_el:
                continue

            name_text = name_el.get_text(strip=True)

            if self.filter_contains and self.filter_contains.upper() not in name_text.upper():
                continue

            items.append(ScrapedItem(
                external_name=name_text,
                external_url=self.base_url,
                external_id=name_text,  # sayfada sabit bir kod olmadığı için isim kimlik görevi görüyor
                raw_price=price_el.get_text(strip=True),
                raw_availability=None,
            ))

        if not items:
            logger.warning("FilteredTableCollector: filtreye uyan satır bulunamadı. URL: %s", self.base_url)

        logger.info("FilteredTableCollector: %d ürün bulundu (%s)", len(items), self.base_url)
        return items
