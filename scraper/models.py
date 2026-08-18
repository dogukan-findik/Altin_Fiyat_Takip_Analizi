from dataclasses import dataclass

@dataclass
class ScrapedItem:
    """Bir collector'ın bir üründen çıkardığı ham veri — henüz DB'ye
    yazılmamış, henüz normalize edilmemiş ara temsil."""
    external_name: str
    external_url: str
    external_id: str | None
    raw_price: str
    raw_availability: str | None = None
