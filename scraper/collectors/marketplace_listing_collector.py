import time
import requests
from bs4 import BeautifulSoup
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT, DETAIL_PAGE_DELAY_SECONDS
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

class MarketplaceListingCollector:
    """n11 gibi pazaryerlerinde tek bir kategori sayfasındaki tüm ürün
    kartlarını çeker. Marka adı her zaman gerçek satıcıyla aynı olmadığı
    için (bkz. GMR/REKOR markalı ürünler, VICTORIAGOLD mağazasından
    satılıyor), fetch_seller_from_detail=True ise her ürünün detay
    sayfasına ayrıca girip GERÇEK satıcı adını çeker."""

    def __init__(self, seller_config: dict):
        self.base_url = seller_config["base_url"]
        self.selectors = seller_config["selectors"]
        self.exclude_terms = [t.lower() for t in seller_config.get("exclude_brand_contains", [])]
        self.known_brands = seller_config.get("known_brands", [])
        self.fetch_seller_from_detail = seller_config.get("fetch_seller_from_detail", False)
        self.detail_seller_selector = seller_config.get("detail_seller_selector")
        self.exclude_title_terms = [t.lower() for t in seller_config.get("exclude_title_contains", [])]

    @retry(max_attempts=3, base_delay_seconds=2.0)
    def _fetch(self, url: str) -> str:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=SCRAPE_TIMEOUT)
        response.raise_for_status()
        return response.text

    def _extract_brand(self, title: str) -> str:
        for brand in self.known_brands:
            if title.lower().startswith(brand.lower()):
                return brand
        return title.split()[0]

    def _fetch_real_seller(self, product_url: str, fallback_brand: str) -> str:
        try:
            html = self._fetch(product_url)
            soup = BeautifulSoup(html, "html.parser")
            seller_el = soup.select_one(self.detail_seller_selector)
            if seller_el:
                return seller_el.get_text(strip=True)
        except Exception as exc:
            logger.warning("Detay sayfasından satıcı çekilemedi (%s): %s", product_url, exc)
        return fallback_brand  # başarısızsa marka adına geri düş

    def collect(self) -> list[ScrapedItem]:
        html = self._fetch(self.base_url)
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for card in soup.select(self.selectors["card"]):
            name_el = card.select_one(self.selectors["name"])
            price_el = card.select_one(self.selectors["price"])
            if not name_el or not price_el:
                continue

            title = name_el.get_text(strip=True)
            
            if any(term in title.lower() for term in self.exclude_terms):
                continue
            if any(term in title.lower() for term in self.exclude_title_terms):
                continue

            brand = self._extract_brand(title)
            url = card.get("href", self.base_url)
            if url.startswith("/"):
                url = "https://www.n11.com" + url
            product_id = card.get("data-prod-id") or url

            items.append(ScrapedItem(
                external_name=title,
                external_url=url,
                external_id=str(product_id),
                raw_price=price_el.get_text(strip=True),
                raw_availability=None,
                seller_name=brand,  # geçici, aşağıda gerekiyorsa gerçeğiyle değiştirilecek
            ))

        if not items:
            logger.warning("MarketplaceListingCollector: hiç kart bulunamadı. URL: %s", self.base_url)
            return items

        if self.fetch_seller_from_detail and self.detail_seller_selector:
            logger.info("Gerçek satıcı adları için %d ürün detay sayfası taranacak...", len(items))
            filtered_items = []

            for item in items:
                real_seller = self._fetch_real_seller(item.external_url, item.seller_name)

                normalized_seller = real_seller.lower().replace(" ", "")
                is_excluded = any(term.replace(" ", "") in normalized_seller for term in self.exclude_terms)

                if is_excluded:
                    logger.info("Kendi satıcımız tespit edildi, atlanıyor: %s (%s)", item.external_name, real_seller)
                    time.sleep(DETAIL_PAGE_DELAY_SECONDS)
                    continue

                item.seller_name = real_seller
                filtered_items.append(item)
                time.sleep(DETAIL_PAGE_DELAY_SECONDS)

            items = filtered_items

        logger.info("MarketplaceListingCollector: %d ürün bulundu (%s)", len(items), self.base_url)
        return items