import json
from playwright.sync_api import sync_playwright
from scraper.config import USER_AGENT, SCRAPE_TIMEOUT
from scraper.parsers.gold_parser import parse_price
from scraper.database import DatabaseManager
from scraper.utils.logger import get_logger
from scraper.utils.retry import retry

logger = get_logger(__name__)

AHLATCIDOVIZ_URL = "https://www.ahlatcidoviz.com.tr/"
AHLATCISTORE_CATEGORY_URL = "https://www.ahlatcistore.com.tr/kategoriler/ziynet-altin"

# Store kategori sayfasındaki isimden hangi Product.Name'e eşleneceği.
CATEGORY_KEYWORDS = [
    ("Cumhuriyet Altını", ["cumhuriyet"]),
    ("Tam Altın", ["tam altın", "tam altin"]),
    ("Yarım Altın", ["yarım altın", "yarim altin"]),
    ("Çeyrek Altın", ["çeyrek altın", "ceyrek altin"]),
]

def match_category(name: str) -> str | None:
    lower = name.lower()
    if "adet" in lower:
        return None  # çoklu paket (2 adet vb.), tekil fiyat değil — atla
    if "yeni tarihli" not in lower:
        return None  # sadece güncel/yeni tarihli varyantı istiyoruz
    for product_name, keywords in CATEGORY_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return product_name
    return None


@retry(max_attempts=3, base_delay_seconds=3.0)
def fetch_gram_price() -> float | None:
    """ahlatcidoviz.com.tr'deki XAU satırından gram altın satış fiyatını çeker."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(AHLATCIDOVIZ_URL, timeout=SCRAPE_TIMEOUT * 1000)
        page.wait_for_selector("table#currencyContainer tbody tr", timeout=SCRAPE_TIMEOUT * 1000)

        price_text = None
        for row in page.query_selector_all("table#currencyContainer tbody tr"):
            code_el = row.query_selector("th")
            if code_el and code_el.inner_text().strip() == "XAU":
                cells = row.query_selector_all("td")
                if len(cells) >= 2:
                    price_text = cells[1].inner_text().strip()  # Satış sütunu
                break

        browser.close()

    if price_text is None:
        logger.warning("ahlatcidoviz.com.tr: XAU satırı bulunamadı.")
        return None

    return parse_price(price_text)


@retry(max_attempts=3, base_delay_seconds=3.0)
def fetch_store_prices() -> dict[str, float]:
    """ahlatcistore.com.tr kategori sayfasından Çeyrek/Yarım/Tam/Cumhuriyet
    'Yeni Tarihli', tekil ürün fiyatlarını çeker."""
    results: dict[str, float] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(AHLATCISTORE_CATEGORY_URL, timeout=SCRAPE_TIMEOUT * 1000)
        page.wait_for_selector("ul.grid li a[href*='/urun/']", timeout=SCRAPE_TIMEOUT * 1000)

        for card in page.query_selector_all("ul.grid li a[href*='/urun/']"):
            name_el = card.query_selector("h3")
            price_el = card.query_selector("p")
            if not name_el or not price_el:
                continue

            name = name_el.get_attribute("title") or name_el.inner_text().strip()
            product_name = match_category(name)
            if product_name is None:
                continue

            price = parse_price(price_el.inner_text().strip())
            if price is None:
                continue

            if product_name not in results:  # aynı kategoriden ilk eşleşeni koru
                results[product_name] = price

        browser.close()

    return results


def run():
    db = DatabaseManager()
    updated = []
    skipped = []

    gram_price = fetch_gram_price()
    if gram_price is not None:
        affected = db.update_own_price("Gram Altın", gram_price)
        if affected > 0:
            updated.append({"product": "Gram Altın", "price": gram_price})
        else:
            logger.warning("'Gram Altın' isimli Product bulunamadı, güncellenemedi.")
            skipped.append("Gram Altın")
    else:
        skipped.append("Gram Altın")

    store_prices = fetch_store_prices()
    for product_name, price in store_prices.items():
        affected = db.update_own_price(product_name, price)
        if affected > 0:
            updated.append({"product": product_name, "price": price})
        else:
            logger.warning("'%s' isimli Product bulunamadı, güncellenemedi.", product_name)
            skipped.append(product_name)

    for product_name, _ in CATEGORY_KEYWORDS:
        if product_name not in store_prices and product_name not in skipped:
            skipped.append(product_name)  # sayfada hiç bulunamadı

    logger.info("OurPrice güncellendi: %s", updated)
    if skipped:
        logger.warning("Güncellenemeyen/bulunamayan ürünler: %s", skipped)

    print(json.dumps({"updated": updated, "skipped": skipped}))


if __name__ == "__main__":
    run()
