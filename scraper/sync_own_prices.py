import json
from scraper.collectors.filtered_table_collector import FilteredTableCollector
from scraper.parsers.gold_parser import parse_price, extract_gram_weight
from scraper.database import DatabaseManager
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

# Her biri ahlatcistore.com.tr'nin bir kategori sayfası. per_gram=True olanlar
# (Bilezik) toplam fiyatı gramaja bölerek normalize edilir.
STORE_CATEGORIES = [
    {"product": "Gram Altın", "url": "https://www.ahlatcistore.com.tr/kategoriler/gram-alltin", "per_gram": False},
    {"product": "Çeyrek Altın", "url": "https://www.ahlatcistore.com.tr/kategoriler/ceyrek-altin", "per_gram": False},
    {"product": "Yarım Altın", "url": "https://www.ahlatcistore.com.tr/kategoriler/yarim-altin", "per_gram": False},
    {"product": "Tam Altın", "url": "https://www.ahlatcistore.com.tr/kategoriler/tam-altin", "per_gram": False},
    {"product": "22 Ayar Bilezik", "url": "https://www.ahlatcistore.com.tr/kategoriler/22-ayar-bilezik", "per_gram": True},
]

# Bu selector'lar daha önce ahlatcistore.com.tr kart yapısından çıkarılmıştı
# (ul.grid li a[href*='/urun/'], h3 title, p fiyat).
STORE_SELECTORS = {
    "row": "ul.grid li a[href*='/urun/']",
    "name": "h3",
    "price": "p",
}


def _pick_first_new_tarihli(items: list) -> tuple[str, float] | None:
    """Aynı kategoride birden fazla ürün olabilir (varyant, adet paketleri).
    'Yeni Tarihli' VE 'Adet' içermeyen ilk tekil ürünü seçer — daha önce
    kurduğumuz kuralın aynısı."""
    for item in items:
        name = item.external_name
        lower = name.lower()
        if "adet" in lower:
            continue
        if "yeni tarihli" not in lower and "24 ayar" not in lower and "22 ayar" not in lower:
            continue
        return name, item.raw_price
    return None


def fetch_store_prices() -> dict[str, float]:
    results: dict[str, float] = {}

    for cat in STORE_CATEGORIES:
        config = {
            "base_url": cat["url"],
            "selectors": STORE_SELECTORS,
            "filter_contains": None,
        }
        collector = FilteredTableCollector(config)

        try:
            items = collector.collect()
        except Exception as exc:
            logger.error("'%s' kategorisi taranamadı (%s): %s", cat["product"], cat["url"], exc)
            continue

        picked = _pick_first_new_tarihli(items)
        if picked is None:
            logger.warning("'%s' için uygun (Yeni Tarihli, tekil) ürün bulunamadı.", cat["product"])
            continue

        name, raw_price = picked
        price = parse_price(raw_price)
        if price is None:
            continue

        if cat["per_gram"]:
            gram = extract_gram_weight(name)
            if gram is None or gram <= 0:
                logger.warning("'%s' için gramaj çıkarılamadı: %s", cat["product"], name)
                continue
            price = round(price / gram, 2)

        results[cat["product"]] = price

    return results


def run():
    db = DatabaseManager()
    updated = []
    skipped = []

    store_prices = fetch_store_prices()
    for product_name, price in store_prices.items():
        affected = db.update_own_price(product_name, price, source_type="Bank")
        if affected > 0:
            updated.append({"product": product_name, "price": price, "source": "Bank"})
        else:
            skipped.append(product_name)

    for cat in STORE_CATEGORIES:
        if cat["product"] not in store_prices and cat["product"] not in skipped:
            skipped.append(cat["product"])

    logger.info("OurPrice güncellendi: %s", updated)
    if skipped:
        logger.warning("Güncellenemeyen/bulunamayan ürünler: %s", skipped)

    print(json.dumps({"updated": updated, "skipped": skipped}))


if __name__ == "__main__":
    run()