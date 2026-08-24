import json
import time
from scraper.collectors.filtered_table_collector import FilteredTableCollector
from scraper.parsers.gold_parser import parse_price, extract_gram_weight
from scraper.database import DatabaseManager
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

# Standart ürünler (tekil)
# NOT: Gram Altın artık gram gram çekiliyor (fetch_gram_altin_prices ile)
STORE_CATEGORIES = [
    {"product": "Çeyrek Altın", "url": "https://www.ahlatcistore.com.tr/kategoriler/ceyrek-altin"},
    {"product": "Yarım Altın", "url": "https://www.ahlatcistore.com.tr/kategoriler/yarim-altin"},
    {"product": "Tam Altın", "url": "https://www.ahlatcistore.com.tr/kategoriler/tam-altin"},
    {"product": "Reşat Altını", "url": "https://www.ahlatcistore.com.tr/kategoriler/resat-altin"},
    {"product": "Ata Altını", "url": "https://www.ahlatcistore.com.tr/kategoriler/ata-lira"},
]

# Bilezikler: Her gramaj ayrı kategoriye gidiyor
BRACELET_URL = "https://www.ahlatcistore.com.tr/kategoriler/22-ayar-bilezik"

# Gram Altın: Her gramaj ayrı kategoriye gidiyor (24 Ayar)
GRAM_ALTIN_URL = "https://www.ahlatcistore.com.tr/kategoriler/24-ayar-gram-alltin"

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


def _collect_all_bracelet_pages() -> list:
    """Kendi sitemizden bilezik kategorisindeki TÜM sayfalardaki ürünleri çeker.
    limit=60 ile sayfa başına maksimum ürün alır, boş sayfa gelene kadar devam eder."""
    all_items = []
    page = 1
    max_pages = 20  # güvenlik sınırı

    while page <= max_pages:
        page_url = f"{BRACELET_URL}?sortBy=price&sortOrder=asc&page={page}&limit=60"
        config = {
            "base_url": page_url,
            "selectors": STORE_SELECTORS,
            "filter_contains": None,
        }
        collector = FilteredTableCollector(config)

        try:
            items = collector.collect()
        except Exception as exc:
            logger.error("Bilezik sayfa %d taranamadı: %s", page, exc)
            break

        if not items:
            logger.info("Bilezik sayfa %d boş geldi, sayfalama bitti.", page)
            break

        all_items.extend(items)
        logger.info("Bilezik sayfa %d: %d ürün çekildi (toplam: %d)", page, len(items), len(all_items))

        # Eğer gelen ürün sayısı limit'ten azsa son sayfadayız
        if len(items) < 60:
            break

        page += 1
        time.sleep(0.5)  # sunucuyu yormamak için kısa bekleme

    return all_items


def fetch_bracelet_prices() -> dict[str, float]:
    """Kendi sitemizden bilezik fiyatlarını gram gram çeker — TÜM sayfaları tarar."""
    results: dict[str, float] = {}

    items = _collect_all_bracelet_pages()
    if not items:
        logger.warning("Bilezik kategorisinden hiç ürün çekilemedi.")
        return results

    logger.info("Toplam %d bilezik ürünü çekildi, işleniyor...", len(items))

    for item in items:
        name = item.external_name
        lower_name = name.lower()

        # "adet" içeren paketleri atla
        if "adet" in lower_name:
            continue

        # Gramajı çıkar
        gram = extract_gram_weight(name)
        if gram is None or gram <= 0:
            continue

        # Fiyatı parse et
        price = parse_price(item.raw_price)
        if price is None:
            continue

        # Kategori adı: "5 Gram Bilezik", "10 Gram Bilezik" vb.
        # TOPLAM FİYAT kaydediliyor (gram başına değil)
        product_key = f"{int(gram) if gram == int(gram) else gram} Gram Bilezik"

        # Aynı gramdan birden fazla varsa, en düşük fiyatı al
        if product_key not in results or price < results[product_key]:
            results[product_key] = price
            logger.info("Bilezik fiyatı: %s = %.2f TL (toplam) (%s)", product_key, price, name)

    return results


def _collect_all_gram_altin_pages() -> list:
    """Kendi sitemizden gram altın kategorisindeki TÜM sayfalardaki ürünleri çeker.
    limit=60 ile sayfa başına maksimum ürün alır, boş sayfa gelene kadar devam eder."""
    all_items = []
    page = 1
    max_pages = 20  # güvenlik sınırı

    while page <= max_pages:
        page_url = f"{GRAM_ALTIN_URL}?sortBy=price&sortOrder=asc&page={page}&limit=60"
        config = {
            "base_url": page_url,
            "selectors": STORE_SELECTORS,
            "filter_contains": None,
        }
        collector = FilteredTableCollector(config)

        try:
            items = collector.collect()
        except Exception as exc:
            logger.error("Gram altın sayfa %d taranamadı: %s", page, exc)
            break

        if not items:
            logger.info("Gram altın sayfa %d boş geldi, sayfalama bitti.", page)
            break

        all_items.extend(items)
        logger.info("Gram altın sayfa %d: %d ürün çekildi (toplam: %d)", page, len(items), len(all_items))

        # Eğer gelen ürün sayısı limit'ten azsa son sayfadayız
        if len(items) < 60:
            break

        page += 1
        time.sleep(0.5)  # sunucuyu yormamak için kısa bekleme

    return all_items


def fetch_gram_altin_prices() -> dict[str, float]:
    """Kendi sitemizden gram altın fiyatlarını gram gram çeker — TÜM sayfaları tarar.
    
    Gram başına fiyat değil, TOPLAM fiyat kaydeder.
    Örn: "5 Gram Altın" = 2.700 TL (5 gram için toplam fiyat)
    """
    results: dict[str, float] = {}

    items = _collect_all_gram_altin_pages()
    if not items:
        logger.warning("Gram altın kategorisinden hiç ürün çekilemedi.")
        return results

    logger.info("Toplam %d gram altın ürünü çekildi, işleniyor...", len(items))

    for item in items:
        name = item.external_name
        lower_name = name.lower()

        # "adet" içeren paketleri atla
        if "adet" in lower_name:
            continue

        # Gramajı çıkar
        gram = extract_gram_weight(name)
        if gram is None or gram <= 0:
            continue

        # Fiyatı parse et
        price = parse_price(item.raw_price)
        if price is None:
            continue

        # Kategori adı: "5 Gram Altın", "10 Gram Altın" vb.
        product_key = f"{int(gram) if gram == int(gram) else gram} Gram Altın"

        # Aynı gramdan birden fazla varsa, en düşük fiyatı al
        if product_key not in results or price < results[product_key]:
            results[product_key] = price
            logger.info("Gram altın fiyatı: %s = %.2f TL (toplam) (%s)", product_key, price, name)

    return results


def fetch_store_prices() -> dict[str, float]:

    """Standart ürünlerin fiyatlarını çeker."""
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

        results[cat["product"]] = price

    return results


def run():
    db = DatabaseManager()
    updated = []
    skipped = []

    # 1) Standart ürünleri çek
    store_prices = fetch_store_prices()
    for product_name, price in store_prices.items():
        affected = db.update_own_price(product_name, price, source_type="Bank")
        if affected > 0:
            updated.append({"product": product_name, "price": price, "source": "Bank"})
        else:
            skipped.append(product_name)

    # 2) Bilezik fiyatlarını gram gram çek
    bracelet_prices = fetch_bracelet_prices()
    for product_name, price in bracelet_prices.items():
        # Eksik gramajları otomatik oluştur
        db.ensure_bracelet_product(product_name)
        affected = db.update_own_price(product_name, price, source_type="Bank")
        if affected > 0:
            updated.append({"product": product_name, "price": price, "source": "Bank"})
        else:
            logger.warning("'%s' güncellenemedi.", product_name)
            skipped.append(product_name)

    # 3) Gram Altın fiyatlarını gram gram çek (TOPLAM FİYAT)
    gram_altin_prices = fetch_gram_altin_prices()
    for product_name, price in gram_altin_prices.items():
        # Eksik gramajları otomatik oluştur
        db.ensure_gram_gold_product(product_name)
        affected = db.update_own_price(product_name, price, source_type="Bank")
        if affected > 0:
            updated.append({"product": product_name, "price": price, "source": "Bank"})
        else:
            logger.warning("'%s' güncellenemedi.", product_name)
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