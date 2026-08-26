from dataclasses import dataclass

@dataclass
class ScrapedItem:
    external_name: str
    external_url: str
    external_id: str | None
    raw_price: str
    raw_availability: str | None = None
    seller_name: str | None = None  # sadece pazaryeri (çoklu satıcı) collector'ları doldurur
    known_seller_id: int | None = None  # yeni: DB'den zaten biliniyorsa, detay sayfasına gitmeden dolar