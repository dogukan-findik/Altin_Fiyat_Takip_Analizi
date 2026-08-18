import sys
import time
import json
from scraper.config import SELLERS, RATE_LIMIT_SECONDS
from scraper.collectors.table_row_collector import TableRowCollector
from scraper.parsers.gold_parser import parse_price, is_in_stock
from scraper.database import DatabaseManager
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

# NOT: SellerId'ler Sellers tablosundaki gerçek Id'lerle eşleşmeli.
# SELLERS config'i sadece "rakip_a" gibi bir anahtar tutuyor, bunu
# DB'deki Sellers.Id'ye eşlemek için burada basit bir sözlük kullanıyoruz.
# Gerçek satıcılar eklendiğinde bu sözlük güncellenmeli (ya da DB'den
# Name'e göre sorgulanmalı — ileri seviye iyileştirme).
SELLER_ID_MAP: dict[str, int] = {
   "garantibbva": 1,  # <-- SSMS'te gerçek Id'yi kontrol edip güncelle
}

def run():
    db = DatabaseManager()
    job_id = db.start_collection_job(job_type="Scheduled")

    processed = success = failed = 0
    error_message = None

    if not SELLERS:
        logger.warning("SELLERS config'i boş — henüz hiçbir satıcı tanımlanmamış. "
                        "config.py içindeki SELLERS sözlüğüne robots.txt kontrolünden "
                        "geçmiş gerçek bir satıcı eklendiğinde scraper veri toplamaya başlayacak.")
        db.complete_collection_job(job_id, 0, 0, 0)
        print(json.dumps({"processed": 0, "success": 0, "failed": 0}))
        return

    try:
        for seller_key, seller_config in SELLERS.items():
            seller_id = SELLER_ID_MAP.get(seller_key)
            if seller_id is None:
                logger.error("'%s' için SELLER_ID_MAP'te eşleşen SellerId yok, atlanıyor.", seller_key)
                continue

            collector = TableRowCollector(seller_config)
            scraped_items = collector.collect()

            try:
                scraped_items = collector.collect()
            except Exception as exc:
                logger.error("'%s' için toplama başarısız: %s", seller_key, exc)
                failed += len(scraped_items) if 'scraped_items' in dir() else 0
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
                db.insert_price(
                    sp_id, price, is_in_stock(item.raw_availability),
                    collection_job_id=job_id
                )
                success += 1

            # Rate limit: satıcı başına max 1 istek/dakika (dokümandaki kural)
            time.sleep(RATE_LIMIT_SECONDS)

        db.complete_collection_job(job_id, processed, success, failed)

    except Exception as exc:
        error_message = str(exc)
        logger.exception("main.py genel hata ile durdu.")
        db.complete_collection_job(job_id, processed, success, failed, error_message=error_message)

    # C# tarafındaki PriceCollectionJob.cs bu satırı stdout'tan okuyup
    # parse edecek (ItemsProcessed/Success/Failed doldurma adımı).
    print(json.dumps({"processed": processed, "success": success, "failed": failed}))

    if error_message:
        sys.exit(1)  # C# tarafı process.ExitCode != 0 kontrolü yapıyor

if __name__ == "__main__":
    run()
