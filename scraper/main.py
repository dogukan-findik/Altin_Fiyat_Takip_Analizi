import sys
import time
import json
import argparse
from scraper.config import SELLERS, RATE_LIMIT_SECONDS
from scraper.collectors.table_row_collector import TableRowCollector
from scraper.collectors.table_row_playwright_collector import TableRowPlaywrightCollector
from scraper.collectors.filtered_table_collector import FilteredTableCollector
from scraper.collectors.filtered_table_playwright_collector import FilteredTablePlaywrightCollector
from scraper.collectors.marketplace_listing_collector import MarketplaceListingCollector
from scraper.parsers.gold_parser import parse_price, extract_gram_weight, categorize_gold_product
from scraper.matchers.product_matcher import ProductMatcher
from scraper.filters.product_filter import ProductFilter
from scraper.validators.price_validator import PriceValidator
from scraper.database import DatabaseManager
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

COLLECTOR_REGISTRY = {
    "table_row": TableRowCollector,
    "table_row_playwright": TableRowPlaywrightCollector,
    "filtered_table": FilteredTableCollector,
    "filtered_table_playwright": FilteredTablePlaywrightCollector,
    "marketplace_listing": MarketplaceListingCollector,
}

SELLER_ID_MAP: dict[str, int] = {
    "garantibbva": 1,
    "qnb": 2,
    "yapikredi": 3,
}

# Bankalarda isim formatı sabit ve temiz olduğu için basit statik eşleme
# yeterli — ProductMatcher'ın esnekliğine ihtiyaç yok.
BANK_PRODUCT_NAME_MAP: dict[str, dict[str, str]] = {
    "garantibbva": {
        "Gram Altın": "Gram Altın",
        "Çeyrek Altın": "Çeyrek Altın",
        "Yarım Altın": "Yarım Altın",
        "Tam Altın": "Tam Altın",
    },
    "qnb": {
        "ALTIN (GRAM)": "Gram Altın",
    },
    "yapikredi": {
        "Gram": "Gram Altın",
        "Çeyrek": "Çeyrek Altın",
        "Yarım": "Yarım Altın",
        "Tam": "Tam Altın",
    },
}


def run(external_job_id: int | None = None):
    db = DatabaseManager()
    job_id = external_job_id if external_job_id is not None else db.start_collection_job(job_type="Manual")

    processed = success = failed = 0
    error_message = None

    if not SELLERS:
        logger.warning("SELLERS config'i boş — henüz hiçbir satıcı tanımlanmamış.")
        db.complete_collection_job(job_id, 0, 0, 0)
        print(json.dumps({"processed": 0, "success": 0, "failed": 0}))
        return

    product_map = db.get_product_name_to_id_map()

    try:
        for seller_key, seller_config in SELLERS.items():
            collector_type = seller_config.get("collector_type")
            collector_cls = COLLECTOR_REGISTRY.get(collector_type)
            if collector_cls is None:
                logger.error("'%s' için bilinmeyen collector_type: %s", seller_key, collector_type)
                continue

            collector = collector_cls(seller_config)

            try:
                scraped_items = collector.collect()
            except Exception as exc:
                logger.error("'%s' için toplama başarısız: %s", seller_key, exc)
                continue

            if collector_type == "marketplace_listing":
                for item in scraped_items:
                    processed += 1

                    # 1. Filtreleme: İstenmeyen ürünleri ayıkla
                    excluded, reason = ProductFilter.should_exclude(item.external_name)
                    if excluded:
                        logger.info("Ürün filtrelendi: %s - Sebep: %s", item.external_name, reason)
                        continue

                    # 2. Temel ürün tipini belirle (22 Ayar Bilezik, Gram Altın vb.)
                    base_product_name = ProductMatcher.match(item.external_name)
                    if base_product_name is None:
                        logger.warning("Ürün eşleştirilemedi, atlanıyor: %s", item.external_name)
                        failed += 1
                        continue

                    # 3. Bilezikler için gram bazlı kategori oluştur
                    #    (5 Gram Bilezik, 10 Gram Bilezik vb.)
                    final_product_name = categorize_gold_product(item.external_name, base_product_name)

                    # 4. Fiyatı parse et
                    price = parse_price(item.raw_price)
                    if price is None:
                        logger.warning("Fiyat parse edilemedi, atlanıyor: %s", item.external_name)
                        failed += 1
                        continue

                    # 5. Gram bazlı ürünlerde gram bilgisini doğrula
                    #    Fiyat işlemesi yapılmaz - toplam fiyat kaydedilir
                    #    (Gram Altın ve Bilezik ikisi de toplam fiyatla kaydedilir)
                    if ProductMatcher.is_gram_based(final_product_name):
                        gram = extract_gram_weight(item.external_name)
                        if gram is None or gram <= 0:
                            logger.warning("Gramaj çıkarılamadı, atlanıyor: %s", item.external_name)
                            failed += 1
                            continue
                        
                        logger.info("Gram bazlı ürün (toplam fiyat): %s (%.2f TL için %.1fg)",
                                    item.external_name, price, gram)

                    # 6. Fiyat validasyonu
                    is_valid, warning = PriceValidator.validate(final_product_name, price)
                    if not is_valid:
                        logger.warning("Fiyat anomalisi: %s - %s", item.external_name, warning)
                        # Reddetmiyoruz, sadece uyarıyoruz — kayıt devam eder.

                    # 7. Ürünü veritabanına kaydet
                    product_id = product_map.get(final_product_name)
                    
                    # Bilezik ve Gram Altın için otomatik ürün oluşturma
                    if product_id is None and "Gram Bilezik" in final_product_name:
                        product_id = db.ensure_bracelet_product(final_product_name)
                        product_map[final_product_name] = product_id
                    elif product_id is None and "Gram Altın" in final_product_name:
                        product_id = db.ensure_gram_gold_product(final_product_name)
                        product_map[final_product_name] = product_id
                    
                    if product_id is None:
                        logger.warning(
                            "'%s' Products tablosunda bulunamadı, atlanıyor.",
                            final_product_name
                        )
                        failed += 1
                        continue

                    # Gram Altın için: eğer doğru gram kategorisi yoksa, 1 Gram fiyatıyla hesapla
                    final_price = price
                    if "Gram Altın" in final_product_name and product_id == product_map.get(final_product_name):
                        # Eğer bu satırlara ulaşıldıysa, ürün ya var ya az önce oluşturuldu
                        # Fiyat doğrudan N11'den geldiğinden, zaten toplam fiyat
                        # Ancak eğer bizde olmayan bir gram varsa, 1g fiyatıyla hesapla
                        pass  # Fiyat zaten doğru (toplam)

                    seller_id = db.get_or_create_seller(item.seller_name, seller_config["base_url"], seller_type="Marketplace")
                    sp_id = db.get_or_create_seller_product(
                        seller_id, item.external_name, item.external_url, item.external_id,
                        product_id=product_id
                    )
                    db.insert_price(sp_id, final_price, True, collection_job_id=job_id)
                    success += 1
                    logger.info("Ürün kaydedildi: '%s' -> '%s' (%.2f TL)",
                                item.external_name, final_product_name, final_price)

            else:
                seller_id = SELLER_ID_MAP.get(seller_key)
                if seller_id is None:
                    logger.error("'%s' için SELLER_ID_MAP'te eşleşen SellerId yok, atlanıyor.", seller_key)
                    continue

                name_map = BANK_PRODUCT_NAME_MAP.get(seller_key, {})
                for item in scraped_items:
                    processed += 1
                    price = parse_price(item.raw_price)
                    if price is None:
                        logger.warning("Fiyat parse edilemedi, atlanıyor: %s", item.external_name)
                        failed += 1
                        continue

                    product_name = name_map.get(item.external_name)
                    product_id = product_map.get(product_name) if product_name else None

                    sp_id = db.get_or_create_seller_product(
                        seller_id, item.external_name, item.external_url, item.external_id,
                        product_id=product_id
                    )
                    db.insert_price(sp_id, price, True, collection_job_id=job_id)
                    success += 1

            time.sleep(RATE_LIMIT_SECONDS)

        db.complete_collection_job(job_id, processed, success, failed)

    except Exception as exc:
        error_message = str(exc)
        logger.exception("main.py genel hata ile durdu.")
        db.complete_collection_job(job_id, processed, success, failed, error_message=error_message)

    print(json.dumps({"processed": processed, "success": success, "failed": failed}))

    if error_message:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", type=int, default=None)
    args = parser.parse_args()
    run(external_job_id=args.job_id)