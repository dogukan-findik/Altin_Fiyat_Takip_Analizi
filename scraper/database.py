import pyodbc
from contextlib import contextmanager
from scraper.config import DB_CONNECTION_STRING
from scraper.utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    def __init__(self, connection_string: str = DB_CONNECTION_STRING):
        if not connection_string:
            raise ValueError("DB_CONNECTION_STRING boş — .env dosyasını kontrol et.")
        self.connection_string = connection_string

    @contextmanager
    def get_connection(self):
        conn = pyodbc.connect(self.connection_string)
        try:
            yield conn
        finally:
            conn.close()

    def start_collection_job(self, job_type: str = "Scheduled") -> int:
        """CollectionJobs tablosuna 'Running' statusunde kayit acar, Id'sini doner."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO CollectionJobs (JobType, Status, StartedAt, TriggeredBy, "
                "ItemsProcessed, ItemsSuccess, ItemsFailed) "
                "OUTPUT INSERTED.Id VALUES (?, 'Running', GETUTCDATE(), 'System', 0, 0, 0)",
                job_type
            )
            job_id = cursor.fetchone()[0]
            conn.commit()
            return job_id

    def complete_collection_job(self, job_id: int, processed: int, success: int, failed: int,
                                  error_message: str | None = None):
        status = "Failed" if error_message else "Completed"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE CollectionJobs SET Status = ?, CompletedAt = GETUTCDATE(), "
                "ItemsProcessed = ?, ItemsSuccess = ?, ItemsFailed = ?, ErrorMessage = ? "
                "WHERE Id = ?",
                status, processed, success, failed, error_message, job_id
            )
            conn.commit()

    def get_or_create_seller_product(self, seller_id: int, external_name: str,
                                       external_url: str, external_id: str | None) -> int:
        """SellerProducts'ta bu external_id daha önce görülmüş mü kontrol eder,
        yoksa yeni (eşleşmemiş) kayıt açar. Var olan ID'yi döner."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Id FROM SellerProducts WHERE SellerId = ? AND ExternalId = ?",
                seller_id, external_id
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE SellerProducts SET LastCollectedAt = GETUTCDATE() WHERE Id = ?",
                    row[0]
                )
                conn.commit()
                return row[0]

            cursor.execute(
                "INSERT INTO SellerProducts (SellerId, ExternalName, ExternalUrl, ExternalId, "
                "IsMatched, IsActive, LastCollectedAt, CreatedAt) "
                "OUTPUT INSERTED.Id VALUES (?, ?, ?, ?, 0, 1, GETUTCDATE(), GETUTCDATE())",
                seller_id, external_name, external_url, external_id
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id

    def insert_price(self, seller_product_id: int, price: float, is_available: bool,
                       currency: str = "TRY", collection_job_id: int | None = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO PriceHistory (SellerProductId, Price, Currency, IsAvailable, "
                "CollectedAt, CollectionJobId) VALUES (?, ?, ?, ?, GETUTCDATE(), ?)",
                seller_product_id, price, currency, is_available, collection_job_id
            )
            conn.commit()
