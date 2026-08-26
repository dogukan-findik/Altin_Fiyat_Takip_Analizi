import os
from dotenv import load_dotenv

load_dotenv()

DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "")
SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", "30"))
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "60"))
DETAIL_PAGE_DELAY_SECONDS = int(os.getenv("DETAIL_PAGE_DELAY_SECONDS", "2"))

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

    "n11_cumhuriyet": {
        "name": "N11 Cumhuriyet Altını",
        "base_url": "https://www.n11.com/altin-ve-gumus/cumhuriyet-altini",
        "collector_type": "marketplace_listing",
        "exclude_brand_contains": ["ahlatcı", "ahlatci"],
        "fetch_seller_from_detail": False,
        "max_pages": None,  # Tüm sayfalar
        "page_delay_seconds": 1,
        "known_brands": [],
        "selectors": {"card": "a.product-item", "name": "h2.product-item-title", "price": "h3.price-currency"},
    },
    "n11_bilezik": {
        "name": "N11 22 Ayar Bilezik",
        "base_url": "https://www.n11.com/altin-ve-gumus/22-ayar-bilezik",
        "collector_type": "marketplace_listing",
        "exclude_brand_contains": ["ahlatcı", "ahlatci"],
        "exclude_title_contains": ["adet"],
        "fetch_seller_from_detail": False,
        "max_pages": 10,
        "page_delay_seconds": 1,
        "known_brands": [],
        "selectors": {"card": "a.product-item", "name": "h2.product-item-title", "price": "h3.price-currency"},
    },
    "n11_kulce_altin": {
        "name": "N11 Külçe Altın",
        "base_url": "https://www.n11.com/altin-ve-gumus/kulce-altin",
        "collector_type": "marketplace_listing",
        "exclude_brand_contains": ["ahlatcı", "ahlatci"],
        "exclude_title_contains": ["adet"],
        "fetch_seller_from_detail": False,
        "max_pages": 5,
        "page_delay_seconds": 1,
        "known_brands": [],
        "selectors": {"card": "a.product-item", "name": "h2.product-item-title", "price": "h3.price-currency"},
    },
    "n11_ziynet": {
        "name": "N11 Ziynet Altın",
        "base_url": "https://www.n11.com/altin-ve-gumus/ziynet-altin",
        "collector_type": "marketplace_listing",
        "exclude_brand_contains": ["ahlatcı", "ahlatci"],
        "exclude_title_contains": ["adet"],
        "fetch_seller_from_detail": False,
        "max_pages": 5,
        "page_delay_seconds": 1,
        "known_brands": [],
        "selectors": {"card": "a.product-item", "name": "h2.product-item-title", "price": "h3.price-currency"},
    },
    "pttavm_altin": {
        "name": "PTTAVM Altın Kampanyası",
        "base_url": "https://www.pttavm.com/kampanyalar/en-fiyat-altin",
        "collector_type": "pttavm_listing",
        "exclude_brand_contains": ["ahlatcı", "ahlatci"],
        "exclude_title_contains": ["adet"],
        "max_pages": None,  # Tüm sayfalar (yaklaşık 3 sayfa)
        "page_delay_seconds": 1.5,
    },
}
