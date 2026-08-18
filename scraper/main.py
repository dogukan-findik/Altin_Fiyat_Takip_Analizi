import sys
import time
import json
from scraper.config import SELLERS, RATE_LIMIT_SECONDS
from scraper.collectors.table_row_collector import TableRowCollector
from scraper.collectors.table_row_playwright_collector import TableRowPlaywrightCollector
from scraper.collectors.filtered_table_collector import FilteredTableCollector
from scraper.collectors.filtered_table_playwright_collector import FilteredTablePlaywrightCollector
from scraper.parsers.gold_parser import parse_price
from scraper.database import DatabaseManager
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

COLLECTOR_REGISTRY = {
    "table_row": TableRowCollector,
    "table_row_playwright": TableRowPlaywrightCollector,
    "filtered_table": FilteredTableCollector,
    "filtered_table_playwright": FilteredTablePlaywrightCollector,
}

SELLER_ID_MAP: dict[str, int] = {
    "garantibbva": 1,  # <-- SSMS'te gerçek Id'yi kontrol edip güncelle
    "qnb": 2,          # <-- SSMS'te gerçek Id'yi kontrol edip güncelle
    "yapikredi": 3,     # <-- SSMS'te gerçek Id'yi kontrol edip güncelle"
}

def run():
    db = DatabaseManager()
    job_id = db.start_collection_job(job_type="Scheduled")

    processed = success = failed = 0
    error_message = None

    if not SELLERS:
        logger.warning("SELLERS config'i boş — henüz hiçbir satıcı tanımlanmamış.")
        db.complete_collection_job(job_id, 0, 0, 0)
        print(json.dumps({"processed": 0, "success": 0, "failed": 0}))
        return

    try:
        for seller_key, seller_config in SELLERS.items():
            seller_id = SELLER_ID_MAP.get(seller_key)
            if seller_id is None:
                logger.error("'%s' için SELLER_ID_MAP'te eşleşen SellerId yok, atlanıyor.", seller_key)
                continue

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

            for item in scraped_items:
                processed += 1
                price = parse_price(item.raw_price)
                if price is None:
                    logger.warning("Fiyat parse edilemedi, atlanıyor: %s", item.external_name)
                    failed += 1
                    continue

                sp_id = db.get_or_create_seller_product(
                    seller_id, item.external_name, item.external_url, item.external_id
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
    run()