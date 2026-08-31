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
                                   external_url: str, external_id: str | None,
                                   product_id: int | None = None) -> int:
        """SellerProducts'ta bu external_id veya normalize edilmiş ExternalUrl daha önce görülmüş mü kontrol eder.
        Mükerrer oluşmasını engeller, eski kayıtları yeni ExternalId ile birleştirir."""
        clean_url = external_url.split('?')[0].strip() if external_url else ""

        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Öncelik: ExternalId ile ara
            row = None
            if external_id:
                cursor.execute(
                    "SELECT Id, ProductId FROM SellerProducts WHERE SellerId = ? AND ExternalId = ?",
                    seller_id, external_id
                )
                row = cursor.fetchone()

            # 2. Öncelik: ExternalId bulunamadıysa clean_url ile ara (Eski URL tabanlı kayıtları yakalamak için)
            if not row and clean_url:
                cursor.execute(
                    "SELECT TOP 1 Id, ProductId FROM SellerProducts WHERE SellerId = ? "
                    "AND (ExternalUrl = ? OR ExternalUrl LIKE ? OR ExternalId = ?)",
                    seller_id, clean_url, clean_url + '?%', clean_url
                )
                row = cursor.fetchone()

            if row:
                sp_id, existing_product_id = row
                target_pid = product_id if product_id is not None else existing_product_id
                is_matched = target_pid is not None

                cursor.execute(
                    "UPDATE SellerProducts SET ProductId = ?, IsMatched = ?, MatchConfidence = ?, "
                    "ExternalName = ?, ExternalUrl = ?, ExternalId = COALESCE(?, ExternalId), "
                    "IsActive = 1, LastCollectedAt = GETUTCDATE() WHERE Id = ?",
                    target_pid, 1 if is_matched else 0, 100 if is_matched else None,
                    external_name, external_url, external_id, sp_id
                )
                conn.commit()
                return sp_id

            is_matched = product_id is not None
            cursor.execute(
                "INSERT INTO SellerProducts (SellerId, ProductId, ExternalName, ExternalUrl, ExternalId, "
                "IsMatched, MatchConfidence, IsActive, LastCollectedAt, CreatedAt) "
                "OUTPUT INSERTED.Id VALUES (?, ?, ?, ?, ?, ?, ?, 1, GETUTCDATE(), GETUTCDATE())",
                seller_id, product_id, external_name, external_url, external_id,
                1 if is_matched else 0, 100 if is_matched else None
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
    
    def update_own_price(self, product_name: str, price: float, source_type: str = "Bank") -> int:
        """OwnPriceBySource tablosuna (ProductId, SourceType) bazında upsert yapar.
        source_type C#'daki SellerType enum string karşılığı olmalı: 'Bank' veya 'Marketplace'."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT Id FROM Products WHERE Name = ?", product_name)
            row = cursor.fetchone()
            if not row:
                return 0
            product_id = row[0]

            cursor.execute(
                "SELECT Id FROM OwnPriceBySource WHERE ProductId = ? AND SourceType = ?",
                product_id, source_type
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    "UPDATE OwnPriceBySource SET Price = ?, UpdatedAt = GETUTCDATE() WHERE Id = ?",
                    price, existing[0]
                )
            else:
                cursor.execute(
                    "INSERT INTO OwnPriceBySource (ProductId, SourceType, Price, UpdatedAt) "
                    "VALUES (?, ?, ?, GETUTCDATE())",
                    product_id, source_type, price
                )

            conn.commit()
            return 1

    def get_or_create_seller(self, name: str, website_url: str | None = None, seller_type: str = "Marketplace") -> int:
        """Sellers tablosunda isimle arar, yoksa oluşturur. Pazaryeri
        collector'larının her item için dinamik satıcı çözmesi için.
        seller_type: 'Bank' veya 'Marketplace' (default: 'Marketplace')"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id FROM Sellers WHERE Name = ?", name)
            row = cursor.fetchone()
            if row:
                return row[0]

            cursor.execute(
                "INSERT INTO Sellers (Name, WebsiteUrl, Type, IsActive, CreatedAt, UpdatedAt) "
                "OUTPUT INSERTED.Id VALUES (?, ?, ?, 1, GETUTCDATE(), GETUTCDATE())",
                name, website_url, seller_type
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            return new_id

    def get_product_name_to_id_map(self) -> dict[str, int]:
        """Products tablosundaki isim -> Id eşlemesini döner. run() başında
        bir kez çağrılıp, tüm scrape döngüsü boyunca cache olarak kullanılır."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id, Name FROM Products")
            return {row[1]: row[0] for row in cursor.fetchall()}

    def ensure_bracelet_product(self, gram_label: str) -> int:
        """Bilezik gramajı için Products tablosunda kayıt yoksa otomatik oluşturur.
        gram_label örn: '15 Gram Bilezik'. Varsa mevcut Id'yi döner."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id FROM Products WHERE Name = ?", gram_label)
            row = cursor.fetchone()
            if row:
                return row[0]

            normalized = gram_label.lower().replace(" ", "")
            description = f"22 Ayar {gram_label}"
            cursor.execute(
                "INSERT INTO Products (Name, NormalizedName, Category, Description, OurPrice, IsActive, CreatedAt) "
                "OUTPUT INSERTED.Id VALUES (?, ?, 'Bilezik', ?, 0, 1, GETUTCDATE())",
                gram_label, normalized, description
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            logger.info("Yeni bilezik ürünü oluşturuldu: %s (Id=%d)", gram_label, new_id)
            return new_id

    def ensure_gram_gold_product(self, gram_label: str) -> int:
        """Gram Altın gramajı için Products tablosunda kayıt yoksa otomatik oluşturur.
        gram_label örn: '5 Gram Altın', '3.5 Gram Altın' vb. Varsa mevcut Id'yi döner."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id FROM Products WHERE Name = ?", gram_label)
            row = cursor.fetchone()
            if row:
                return row[0]

            normalized = gram_label.lower().replace(" ", "")
            description = f"24 Ayar {gram_label}"
            cursor.execute(
                "INSERT INTO Products (Name, NormalizedName, Category, Description, OurPrice, IsActive, CreatedAt) "
                "OUTPUT INSERTED.Id VALUES (?, ?, 'Gram Altın', ?, 0, 1, GETUTCDATE())",
                gram_label, normalized, description
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            logger.info("Yeni gram altın ürünü oluşturuldu: %s (Id=%d)", gram_label, new_id)
            return new_id

    def ensure_multi_pack_or_special_product(self, product_name: str) -> int:
        """Çoklu adet paketleri ('3 Adet Çeyrek Altın', '5 Adet Tam Altın') veya özel altınlar
        ('Gremse Altın', 'Beşli Altın') için Products tablosunda kayıt yoksa otomatik oluşturur.
        Varsa mevcut Id'yi döner."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Id FROM Products WHERE Name = ?", product_name)
            row = cursor.fetchone()
            if row:
                return row[0]

            import re
            m_pack = re.match(r"^(\d+)\s*Adet\s*(.+)$", product_name, re.IGNORECASE)
            category = "Sarrafiye"
            calc_our_price = 0.0

            if m_pack:
                qty = int(m_pack.group(1))
                base_name = m_pack.group(2).strip()
                # Temel ürünün birim fiyatını öğren
                cursor.execute(
                    "SELECT COALESCE((SELECT TOP 1 Price FROM OwnPriceBySource WHERE ProductId = p.Id AND SourceType = 'Marketplace'), p.OurPrice) "
                    "FROM Products p WHERE p.Name = ?", base_name
                )
                base_row = cursor.fetchone()
                if base_row and base_row[0]:
                    calc_our_price = float(base_row[0]) * qty
            elif product_name == "Gremse Altın":
                # Çeyrek altının 10 katı (2.5 adet tam altın = 10 çeyrek altın)
                cursor.execute("SELECT OurPrice FROM Products WHERE Name = 'Çeyrek Altın'")
                base_row = cursor.fetchone()
                if base_row and base_row[0]:
                    calc_our_price = float(base_row[0]) * 10
            elif product_name == "Beşli Altın":
                # Tam altının 5 katı
                cursor.execute("SELECT OurPrice FROM Products WHERE Name = 'Tam Altın'")
                base_row = cursor.fetchone()
                if base_row and base_row[0]:
                    calc_our_price = float(base_row[0]) * 5

            normalized = product_name.lower().replace(" ", "")
            description = f"{product_name} (Sarrafiye)"

            cursor.execute(
                "INSERT INTO Products (Name, NormalizedName, Category, Description, OurPrice, IsActive, CreatedAt) "
                "OUTPUT INSERTED.Id VALUES (?, ?, ?, ?, ?, 1, GETUTCDATE())",
                product_name, normalized, category, description, calc_our_price
            )
            new_id = cursor.fetchone()[0]

            if calc_our_price > 0:
                cursor.execute(
                    "INSERT INTO OwnPriceBySource (ProductId, SourceType, Price, UpdatedAt) VALUES (?, 'Marketplace', ?, GETUTCDATE())",
                    new_id, calc_our_price
                )

            conn.commit()
            logger.info("Yeni sarrafiye/paket ürünü oluşturuldu: %s (Id=%d, OurPrice=%.2f TL)", product_name, new_id, calc_our_price)
            return new_id

    def get_unit_gram_gold_price(self) -> float | None:
        """1 Gram Altın (yoksa Gram Altın) birim fiyatını OwnPriceBySource / OurPrice'dan döner."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for name in ("1 Gram Altın", "Gram Altın"):
                cursor.execute(
                    "SELECT COALESCE("
                    "(SELECT TOP 1 ops.Price FROM OwnPriceBySource ops "
                    " WHERE ops.ProductId = p.Id AND ops.SourceType = 'Bank'),"
                    " p.OurPrice) "
                    "FROM Products p WHERE p.Name = ?",
                    name,
                )
                row = cursor.fetchone()
                if row and row[0] and float(row[0]) > 0:
                    return float(row[0])
        return None

    def list_seller_products_for_product_name(self, product_name: str) -> list[tuple[int, str]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sp.Id, sp.ExternalName FROM SellerProducts sp "
                "INNER JOIN Products p ON p.Id = sp.ProductId WHERE p.Name = ?",
                product_name,
            )
            return [(row[0], row[1]) for row in cursor.fetchall()]

    def clear_seller_product_match(self, seller_product_id: int, deactivate: bool = True):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if deactivate:
                cursor.execute(
                    "UPDATE SellerProducts SET ProductId = NULL, IsMatched = 0, MatchConfidence = NULL, "
                    "IsActive = 0 WHERE Id = ?",
                    seller_product_id,
                )
            else:
                cursor.execute(
                    "UPDATE SellerProducts SET ProductId = NULL, IsMatched = 0, MatchConfidence = NULL "
                    "WHERE Id = ?",
                    seller_product_id,
                )
            conn.commit()

    def update_seller_product_match(self, seller_product_id: int, product_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE SellerProducts SET ProductId = ?, IsMatched = 1, MatchConfidence = 100 "
                "WHERE Id = ?",
                product_id, seller_product_id,
            )
            conn.commit()

    def deactivate_product_by_name(self, product_name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Products SET IsActive = 0 WHERE Name = ?",
                product_name,
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_gram_gold_price(self, gram: float) -> float | None:
        """Geriye dönük: 1 gram fiyatını döner. gram parametresi kullanılmaz."""
        return self.get_unit_gram_gold_price()

