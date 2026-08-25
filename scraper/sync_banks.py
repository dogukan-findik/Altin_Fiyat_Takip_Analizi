import sys
import time
import json
import argparse
from scraper.config import SELLERS, RATE_LIMIT_SECONDS
from scraper.collectors.table_row_collector import TableRowCollector
from scraper.collectors.table_row_playwright_collector import TableRowPlaywrightCollector
from scraper.collectors.filtered_table_collector import FilteredTableCollector
from scraper.collectors.filtered_table_playwright_collector import FilteredTablePlaywrightCollector
from scraper.parsers.gold_parser import parse_price
from scraper.database import DatabaseManager
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

# Sadece banka collector tipleri — pazaryeri (marketplace_listing) burada
# YOK, o main.py'nin sorumluluğunda kalıyor. Bankalar hafif ve hızlı
# olduğu için (sayfalama yok, detay taraması yok) 5 dakikada bir
# çalıştırılabilir, pazaryeri ise ayrı ve yavaş kalıyor.
BANK_COLLECTOR_TYPES = {
    "table_row",
    "table_row_playwright",
    "filtered_table",
    "filtered_table_playwright",
}

COLLECTOR_REGISTRY = {
    "table_row": TableRowCollector,
    "table_row_playwright": TableRowPlaywrightCollector,
    "filtered_table": FilteredTableCollector,
    "filtered_table_playwright": FilteredTablePlaywrightCollector,
}

SELLER_ID_MAP: dict[str, int] = {
    "garantibbva": 1,
    "qnb": 2,
    "yapikredi": 3,
}

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

    product_map = db.get_product_name_to_id_map()

    bank_sellers = {
        key: cfg for key, cfg in SELLERS.items()
        if cfg.get("collector_type") in BANK_COLLECTOR_TYPES
    }

    if not bank_sellers:
        logger.warning("config.py'de banka tanımlı değil (BANK_COLLECTOR_TYPES eşleşmedi).")
        db.complete_collection_job(job_id, 0, 0, 0)
        print(json.dumps({"processed": 0, "success": 0, "failed": 0}))
        return

    try:
        for seller_key, seller_config in bank_sellers.items():
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
        logger.exception("sync_banks.py genel hata ile durdu.")
        db.complete_collection_job(job_id, processed, success, failed, error_message=error_message)

    print(json.dumps({"processed": processed, "success": success, "failed": failed}))

    if error_message:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", type=int, default=None)
    args = parser.parse_args()
    run(external_job_id=args.job_id)
