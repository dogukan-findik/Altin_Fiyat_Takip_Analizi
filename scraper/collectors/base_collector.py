from abc import ABC, abstractmethod
from scraper.models import ScrapedItem

class BaseCollector(ABC):
    """Her collector (Playwright, requests, ileride başka bir yöntem)
    bu arayüzü uygulamalı. Böylece main.py hangi collector'ın hangi
    satıcıda kullanıldığını bilmeden aynı şekilde çağırabilir."""

    def __init__(self, seller_config: dict):
        self.seller_config = seller_config
        self.base_url = seller_config["base_url"]
        self.selectors = seller_config["selectors"]

    @abstractmethod
    def collect(self) -> list[ScrapedItem]:
        """Satıcı sayfasından ham ürün listesini döner."""
        raise NotImplementedError
