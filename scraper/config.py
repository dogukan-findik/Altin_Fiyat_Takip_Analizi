import os
from dotenv import load_dotenv

load_dotenv()

DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "")
SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", "30"))
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "60"))

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 "
    "AltinFiyatTakipAnalizi-Scraper/1.0 (+iletisim: staj@ahlatci.com)"
)

# Her satıcı burada tanımlanır. Şimdilik BOŞ — gerçek bir satıcı
# eklemeden önce o satıcının robots.txt'i kontrol edilmeli (bkz.
# doküman EK-C: Hukuki ve Teknik Notlar). Sahte/örnek bir satıcı
# URL'si buraya yazmıyorum çünkü gerçek olmayan veri normalize
# etme riskini istemiyorum.
SELLERS: dict = {
    "garantibbva": {
        "name": "Garanti BBVA",
        "base_url": "https://www.garantibbva.com.tr/altin-kurlari",
        "collector_type": "table_row_playwright",
        "selectors": {
            "row": "tr[data-id]",
            "bid": "td[data-id='bid']",
            "ask": "td[data-id='ask']",
        },
        "symbol_map": {
            "GLDGR": "Gram Altın",
            "SGLDC": "Çeyrek Altın",
            "SGLDY": "Yarım Altın",
            "SGZIYNET": "Tam Altın",
            "SCUM": "Cumhuriyet Altını",
        },
    },
    "qnb": {
        "name": "QNB Finansbank",
        "base_url": "https://www.qnb.com.tr/kur-bilgileri",
        "collector_type": "filtered_table_playwright",
        "filter_contains": "ALTIN",
        "selectors": {
            "row": "table.table.default.table-zebra tbody tr",
            "name": "td:nth-of-type(2)",
            "price": "td:nth-of-type(4)",
        },
    },
    "yapikredi": {
        "name": "Yapı Kredi",
        "base_url": "https://www.yapikredi.com.tr/yatirimci-kosesi/altin-bilgileri",
        "collector_type": "filtered_table",  # önce statik dene, JS render çıkarsa _playwright'a çeviririz
        "selectors": {
            "row": "table#credit-table tbody tr",
            "name": "td:nth-of-type(1)",
            "price": "td:nth-of-type(3)",  # 3. sütun = Satış(TL)
        },
    },
}
