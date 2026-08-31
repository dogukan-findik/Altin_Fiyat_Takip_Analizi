import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scraper.collectors.base_collector import BaseCollector
from scraper.models import ScrapedItem
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.utils.retry import retry
from scraper.utils.logger import get_logger

logger = get_logger(__name__)


class PazaramaListingCollector(BaseCollector):
    """Pazarama arama sayfalarındaki altın ürünlerini requests ile hızlıca çeker.
    
    Pazarama doğrudan SSR (Server-Side Rendering) HTML sunduğu için Playwright
    çalıştırmaya gerek kalmadan saniyeler içinde tüm sayfaları tarar."""

    def __init__(self, seller_config: dict):
        self.seller_config = seller_config
        self.base_url = seller_config["base_url"]
        self.exclude_terms = [t.lower() for t in seller_config.get("exclude_brand_contains", [])]
        self.exclude_title_terms = [t.lower() for t in seller_config.get("exclude_title_contains", [])]
        self.max_pages = seller_config.get("max_pages", 5)
        self.page_delay = seller_config.get("page_delay_seconds", 1.0)

    @retry(max_attempts=3, base_delay_seconds=2.0)
    def _fetch_html(self, url: str) -> str:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        resp = requests.get(url, headers=headers, timeout=SCRAPE_TIMEOUT)
        resp.raise_for_status()
        return resp.text

    def _extract_seller_name(self, title: str) -> str:
        """Pazarama ürün başlıkları genellikle satıcı/marka ile başlar."""
        known_sellers = [
            "AltınDenizi", "AltinDenizi", "AgaKulche", "Aga_Kulche", "Tuğrul Kuyumculuk",
            "Tugrul Kuyumculuk", "Nadir Gold", "Ahlatcı", "Ahlatci", "Harem Altın",
            "Koleksiyonluk", "Sevim Gold", "Victoria Gold"
        ]
        lower_title = title.lower()
        for seller in known_sellers:
            if lower_title.startswith(seller.lower()):
                return seller
        return title.split()[0]

    def _extract_page_items(self, html: str) -> list[ScrapedItem]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("a[title][href*='-p-']")
        items: list[ScrapedItem] = []

        for a in cards:
            title_el = a.select_one("[data-testid='product-card-title']")
            price_el = a.select_one("[data-testid='base-product-card-price-container']")
            if not title_el or not price_el:
                continue

            title = title_el.get_text(strip=True)
            lower_title = title.lower()

            # Takı / Aksesuar / Çoklu adet filtresi
            if any(term in lower_title for term in self.exclude_title_terms):
                continue

            href = a.get("href", "")
            if href.startswith("/"):
                href = urljoin("https://www.pazarama.com", href)

            # Satıcı adı
            seller_name = self._extract_seller_name(title)
            normalized_seller = seller_name.lower().replace(" ", "")

            # Kendi mağazamız filtresi (Ahlatcı)
            if any(term.replace(" ", "") in normalized_seller for term in self.exclude_terms) or "ahlatc" in lower_title:
                logger.debug("Pazarama: Kendi ürünümüz atlandı: %s (%s)", title, seller_name)
                continue

            # Fiyat çıkarma (Sepette indirimli fiyatı varsa en son geçen fiyatı al)
            price_text = price_el.get_text(" ", strip=True)
            prices = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*(?:TL|₺)?', price_text)
            final_price = prices[-1] if prices else price_text

            # Ürün ID'si
            m = re.search(r'-p-([A-Za-z0-9]+)', href)
            product_id = m.group(1) if m else href

            items.append(
                ScrapedItem(
                    external_name=title,
                    external_url=href,
                    external_id=str(product_id),
                    raw_price=final_price,
                    raw_availability=None,
                    seller_name=seller_name,
                )
            )

        return items

    def collect(self) -> list[ScrapedItem]:
        all_items: list[ScrapedItem] = []
        page = 1

        while True:
            if self.max_pages and page > self.max_pages:
                logger.info("Pazarama: Max sayfa limitine ulaşıldı (%d), durduruluyor.", self.max_pages)
                break

            url = f"{self.base_url}&sayfa={page}" if page > 1 else self.base_url
            logger.info("Pazarama Sayfa %d çekiliyor: %s", page, url)

            try:
                html = self._fetch_html(url)
                page_items = self._extract_page_items(html)

                if not page_items:
                    logger.info("Pazarama Sayfa %d'de ürün bulunamadı, pagination sonu.", page)
                    break

                all_items.extend(page_items)
                logger.info("Pazarama Sayfa %d: %d ürün bulundu (Toplam: %d)", page, len(page_items), len(all_items))

                page += 1
                time.sleep(self.page_delay)
            except Exception as exc:
                logger.error("Pazarama Sayfa %d çekilirken hata: %s", page, exc)
                break

        logger.info("PazaramaListingCollector: TOPLAM %d ürün başarıyla toplandı (%s)", len(all_items), self.base_url)
        return all_items
