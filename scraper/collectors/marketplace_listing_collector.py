import time
import requests
from bs4 import BeautifulSoup
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT, DETAIL_PAGE_DELAY_SECONDS
from scraper.parsers.gold_parser import resolve_listing_price_text
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

logger = get_logger(__name__)

class MarketplaceListingCollector:
    """n11 gibi pazaryerlerinde kategori sayfalarındaki tüm ürünleri
    pagination ile çeker. Marka adı her zaman gerçek satıcıyla aynı olmadığı
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
        self.max_pages = seller_config.get("max_pages", None)  # None = tüm sayfalar
        self.page_delay = seller_config.get("page_delay_seconds", 2)

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

    def _build_page_url(self, page_num: int) -> str:
        """N11 pagination formatı: ?pg=2, ?pg=3 vb."""
        parsed = urlparse(self.base_url)
        query_params = parse_qs(parsed.query)
        query_params['pg'] = [str(page_num)]
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    def _collect_page(self, url: str) -> list[ScrapedItem]:
        """Tek bir sayfadaki ürünleri toplar."""
        html = self._fetch(url)
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

            primary_price = price_el.get_text(" ", strip=True)
            card_text = card.get_text(" ", strip=True)
            raw_price = resolve_listing_price_text(primary_price, card_text)

            items.append(ScrapedItem(
                external_name=title,
                external_url=url,
                external_id=str(product_id),
                raw_price=raw_price,
                raw_availability=None,
                seller_name=brand,  # geçici, aşağıda gerekiyorsa gerçeğiyle değiştirilecek
            ))

        return items

    def collect(self) -> list[ScrapedItem]:
        """Tüm sayfaları dolaşıp ürünleri toplar."""
        all_items = []
        page = 1

        while True:
            if self.max_pages and page > self.max_pages:
                logger.info("Max sayfa limitine ulaşıldı (%d), durduruluyor.", self.max_pages)
                break

            url = self.base_url if page == 1 else self._build_page_url(page)
            logger.info("Sayfa %d çekiliyor: %s", page, url)

            try:
                page_items = self._collect_page(url)
                
                if not page_items:
                    logger.info("Sayfa %d'de ürün bulunamadı, pagination sonu.", page)
                    break
                
                all_items.extend(page_items)
                logger.info("Sayfa %d: %d ürün bulundu (toplam: %d)", page, len(page_items), len(all_items))
                
                page += 1
                
                # Sayfa arası bekleme
                if page > 2:  # İlk sayfadan sonra bekle
                    time.sleep(self.page_delay)
                    
            except Exception as exc:
                logger.error("Sayfa %d çekilirken hata: %s", page, exc)
                break

        if not all_items:
            logger.warning("MarketplaceListingCollector: hiç ürün bulunamadı. URL: %s", self.base_url)
            return all_items

        if self.fetch_seller_from_detail and self.detail_seller_selector:
            logger.info("Gerçek satıcı adları için %d ürün detay sayfası taranacak...", len(all_items))
            filtered_items = []

            for item in all_items:
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

            all_items = filtered_items

        logger.info("MarketplaceListingCollector: TOPLAM %d ürün bulundu (%s)", len(all_items), self.base_url)
        return all_items
