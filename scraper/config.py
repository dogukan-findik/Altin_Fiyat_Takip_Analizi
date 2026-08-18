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
        "selectors": {
            "row": "tr[data-id]",
            "bid": "td[data-id='bid']",
            "ask": "td[data-id='ask']",
        },
        "symbol_map": {
            "GLDGR": "Gram Altın",       # doğrulandı (senin HTML'inden)
            "SGLDC": "Çeyrek Altın",     # tahmin — doğrulanmadı
            "SGLDY": "Yarım Altın",      # tahmin — doğrulanmadı
            "SGZIYNET": "Tam Altın",     # tahmin — doğrulanmadı
            "SCUM": "Cumhuriyet Altını", # tahmin — doğrulanmadı
        },
    },
}
