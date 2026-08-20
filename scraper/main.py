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
from scraper.parsers.gold_parser import parse_price, extract_gram_weight
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

def run(external_job_id: int | None = None):
    db = DatabaseManager()

   # C# (Scheduler) tetiklediyse kendi açtığı job_id'yi --job-id ile gönderir,
    # biz onu kullanırız (ikinci bir satır açmayız). Elle/terminalden
    # çalıştırıldığında (external_job_id=None) scraper kendi job'ını kendisi açar.
    job_id = external_job_id if external_job_id is not None else db.start_collection_job(job_type="Manual")

    processed = success = failed = 0
    error_message = None

    if not SELLERS:
        logger.warning("SELLERS config'i boş — henüz hiçbir satıcı tanımlanmamış.")
        db.complete_collection_job(job_id, 0, 0, 0)
        print(json.dumps({"processed": 0, "success": 0, "failed": 0}))
        return

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
                # Çoklu satıcı: her item kendi Seller'ını (marka) taşıyor
                price_unit = seller_config.get("price_unit", "total")
                for item in scraped_items:
                    processed += 1
                    price = parse_price(item.raw_price)
                    if price is None:
                        logger.warning("Fiyat parse edilemedi, atlanıyor: %s", item.external_name)
                        failed += 1
                        continue

                    if price_unit == "per_gram":
                        gram = extract_gram_weight(item.external_name)
                        if gram is None or gram <= 0:
                            logger.warning("Gramaj çıkarılamadı, atlanıyor: %s", item.external_name)
                            failed += 1
                            continue
                        price = round(price / gram, 2)

                    seller_id = db.get_or_create_seller(item.seller_name, seller_config["base_url"])
                    sp_id = db.get_or_create_seller_product(
                        seller_id, item.external_name, item.external_url, item.external_id
                    )
                    db.insert_price(sp_id, price, True, collection_job_id=job_id)
                    success += 1
            else:
                # Tekil satıcı: sabit SELLER_ID_MAP (bankalar)
                seller_id = SELLER_ID_MAP.get(seller_key)
                if seller_id is None:
                    logger.error("'%s' için SELLER_ID_MAP'te eşleşen SellerId yok, atlanıyor.", seller_key)
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--job-id", type=int, default=None,
        help="C# Scheduler'ın önceden açtığı CollectionJob Id'si. "
             "Verilmezse scraper kendi job kaydını kendisi açar (manuel çalıştırma)."
    )
    args = parser.parse_args()
    run(external_job_id=args.job_id)