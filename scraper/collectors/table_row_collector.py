import requests
from bs4 import BeautifulSoup
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

class TableRowCollector:
    """Garanti BBVA gibi, tablo satırının 'ürün kimliği'ni metin olarak
    değil bir data-attribute (data-id) üzerinden taşıyan siteler için.
    BaseCollector'ın metin-tabanlı 'name' selector varsayımı burada
    işe yaramıyor, isim eşlemesi config'teki symbol_map'ten okunuyor."""

    def __init__(self, seller_config: dict):
        self.base_url = seller_config["base_url"]
        self.selectors = seller_config["selectors"]
        self.symbol_map: dict[str, str] = seller_config["symbol_map"]

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
            data_id = row.get("data-id")
            if not data_id or data_id not in self.symbol_map:
                continue  # takip etmediğimiz/bilmediğimiz bir ürün türü, atla

            ask_el = row.select_one(self.selectors["ask"])
            if not ask_el:
                continue

            items.append(ScrapedItem(
                external_name=self.symbol_map[data_id],
                external_url=self.base_url,
                external_id=data_id,
                raw_price=ask_el.get_text(strip=True),
                raw_availability=None,
            ))

        if not items:
            logger.warning(
                "TableRowCollector: hiç satır bulunamadı — sayfa JS ile render "
                "ediliyor olabilir, Playwright'a geçmek gerekebilir. URL: %s",
                self.base_url
            )

        logger.info("TableRowCollector: %d ürün bulundu (%s)", len(items), self.base_url)
        return items
