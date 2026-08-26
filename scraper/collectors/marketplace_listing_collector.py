import time
import json
import requests
from bs4 import BeautifulSoup
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.parsers.gold_parser import resolve_listing_price_text
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = get_logger(__name__)


class MarketplaceListingCollector:
    """N11 gibi pazaryerlerinde kategori sayfalarındaki tüm ürünleri
    pagination ile çeker.
    
    Sayfa içindeki window.model JSON'unda her ürünün başlığı, indirimli fiyatı,
    linki ve GERÇEK SATICI ADI (sellerNickName) doğrudan yer alır.
    Bu sayede detay sayfalarına tek tek girmeye gerek kalmadan saniyeler içinde
    tüm liste eksiksiz toplanır."""

    def __init__(self, seller_config: dict):
        self.base_url = seller_config["base_url"]
        self.selectors = seller_config.get("selectors", {})
        self.exclude_terms = [t.lower() for t in seller_config.get("exclude_brand_contains", [])]
        self.known_brands = seller_config.get("known_brands", [])
        self.fetch_seller_from_detail = seller_config.get("fetch_seller_from_detail", False)
        self.detail_seller_selector = seller_config.get("detail_seller_selector")
        self.exclude_title_terms = [t.lower() for t in seller_config.get("exclude_title_contains", [])]
        self.max_pages = seller_config.get("max_pages", None)  # None = tüm sayfalar
        self.page_delay = seller_config.get("page_delay_seconds", 1.0)

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

    def _build_page_url(self, page_num: int) -> str:
        """N11 pagination formatı: ?pg=2, ?pg=3 vb."""
        parsed = urlparse(self.base_url)
        query_params = parse_qs(parsed.query)
        query_params['pg'] = [str(page_num)]
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    def _extract_from_window_model(self, html: str) -> list[ScrapedItem] | None:
        """Sayfa kaynak kodundaki window.model JSON'undan ürünleri doğrudan çeker."""
        soup = BeautifulSoup(html, "html.parser")
        for s in soup.find_all("script"):
            txt = s.string or s.text or ""
            if "window.model" in txt:
                try:
                    idx = txt.find("window.model")
                    start = txt.find("{", idx)
                    decoder = json.JSONDecoder()
                    model, _ = decoder.raw_decode(txt[start:])
                    search_results = model.get("searchResults", [])
                    if not search_results or not isinstance(search_results, list):
                        continue

                    items: list[ScrapedItem] = []
                    for prod in search_results:
                        title = (prod.get("title") or prod.get("subtitle") or "").strip()
                        if not title:
                            continue

                        # Başlık / Adet filtresi
                        lower_title = title.lower()
                        if any(term in lower_title for term in self.exclude_title_terms):
                            continue

                        # Satıcı adı (N11'deki gerçek mağaza adı)
                        seller_name = prod.get("sellerNickName") or prod.get("brand") or self._extract_brand(title)
                        seller_name = seller_name.strip()

                        # Kendi satıcımız kontrolü
                        normalized_seller = seller_name.lower().replace(" ", "")
                        if any(term.replace(" ", "") in normalized_seller for term in self.exclude_terms):
                            continue

                        # Fiyat belirleme
                        price_val = prod.get("displayPrice") or prod.get("price") or prod.get("mobilePrice")
                        if price_val:
                            raw_price = f"{float(price_val):.2f}"
                        else:
                            raw_price = prod.get("displayPriceStr") or prod.get("priceStr") or ""

                        # URL
                        url = prod.get("url") or prod.get("urlWithoutSellerShop") or self.base_url
                        if url.startswith("/"):
                            url = "https://www.n11.com" + url

                        product_id = prod.get("productId") or prod.get("id") or url

                        items.append(
                            ScrapedItem(
                                external_name=title,
                                external_url=url,
                                external_id=str(product_id),
                                raw_price=str(raw_price),
                                raw_availability=None,
                                seller_name=seller_name,
                            )
                        )

                    return items
                except Exception as exc:
                    logger.debug("window.model JSON decode hatası: %s", exc)

        return None

    def _collect_page_dom(self, html: str) -> list[ScrapedItem]:
        """window.model bulunamazsa DOM üzerinden fallback toplama."""
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for card in soup.select(self.selectors.get("card", "a.product-item")):
            name_el = card.select_one(self.selectors.get("name", "h2.product-item-title"))
            price_el = card.select_one(self.selectors.get("price", "h3.price-currency"))
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

            items.append(
                ScrapedItem(
                    external_name=title,
                    external_url=url,
                    external_id=str(product_id),
                    raw_price=raw_price,
                    raw_availability=None,
                    seller_name=brand,
                )
            )

        return items

    def _collect_page(self, url: str) -> list[ScrapedItem]:
        """Tek bir sayfadaki ürünleri toplar (Önce hızlı JSON model, yoksa DOM fallback)."""
        html = self._fetch(url)

        # 1. Hızlı JSON modelinden topla (0.1 saniye & gerçek satıcı adıyla)
        items = self._extract_from_window_model(html)
        if items is not None:
            return items

        # 2. DOM fallback
        return self._collect_page_dom(html)

    def collect(self) -> list[ScrapedItem]:
        """Tüm sayfaları dolaşıp ürünleri hızla toplar."""
        all_items = []
        page = 1

        while True:
            if self.max_pages and page > self.max_pages:
                logger.info("N11: Max sayfa limitine ulaşıldı (%d), durduruluyor.", self.max_pages)
                break

            url = self.base_url if page == 1 else self._build_page_url(page)
            logger.info("N11 sayfa %d çekiliyor: %s", page, url)

            try:
                page_items = self._collect_page(url)
                if not page_items:
                    logger.info("Sayfa %d'de ürün bulunamadı, pagination sonu.", page)
                    break

                all_items.extend(page_items)
                logger.info("Sayfa %d: %d ürün bulundu (toplam: %d)", page, len(page_items), len(all_items))

                page += 1
                if page > 2:
                    time.sleep(self.page_delay)

            except Exception as exc:
                logger.error("Sayfa %d çekilirken hata: %s", page, exc)
                break

        logger.info("MarketplaceListingCollector: TOPLAM %d ürün bulundu (%s)", len(all_items), self.base_url)
        return all_items
