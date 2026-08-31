class PriceValidator:
    """Kaydedilecek fiyatın beklenen aralık dışında olup olmadığını
    kontrol eder. Anomali tespit edilirse kaydı REDDETMEZ, sadece
    çağıran tarafa loglanacak bir uyarı döner — piyasa gerçekten
    böyle hareket etmiş olabilir, scraper bunu kesin yanlış sayamaz.

    NOT: Aralıklar sabit/statik yazılmıştır, gerçek zamanlı bir referans
    fiyata bağlı değildir — piyasa önemli ölçüde hareket ederse bu
    aralıkların elle güncellenmesi gerekir."""

    # (min, max) TL — tüm ürünlerde TOPLAM FİYAT
    # Gram Altın ve Gram Bilezik: kategori adları "X Gram Altın" / "X Gram Bilezik" şeklinde
    # olduğu için bunlar dinamiktir. Genel aralıklar kullanılır.
    _RANGES: dict[str, tuple[float, float]] = {
        "Gram Altın": (500, 1000000),      # 1g ~ 100g arası (toplam fiyat)
        "22 Ayar Bilezik": (3000, 1000000), # 3g ~ 100g arası (toplam fiyat)
        "Çeyrek Altın": (9000, 25000),
        "Yarım Altın": (18000, 45000),
        "Tam Altın": (30000, 85000),
        "Reşat Altını": (30000, 85000),
        "Ata Altını": (30000, 85000),
        "Gremse Altın": (85000, 220000),   # 2.5'luk altın (~120.000 TL)
        "Beşli Altın": (180000, 550000),   # 5'lik altın (~250.000 TL)
    }

    @classmethod
    def _get_product_base_name_and_multiplier(cls, product_name: str) -> tuple[str, int]:
        """'5 Gram Altın' → ('Gram Altın', 1)
        '3 Adet Çeyrek Altın' → ('Çeyrek Altın', 3)
        '10 Adet Tam Altın' → ('Tam Altın', 10)
        """
        import re
        m_pack = re.match(r"^(\d+)\s*Adet\s*(.+)$", product_name, re.IGNORECASE)
        if m_pack:
            qty = int(m_pack.group(1))
            base = m_pack.group(2).strip()
            return base, qty

        if "Gram Altın" in product_name:
            return "Gram Altın", 1
        if "Gram Bilezik" in product_name:
            return "22 Ayar Bilezik", 1

        return product_name, 1

    @classmethod
    def validate(cls, product_name: str, price: float) -> tuple[bool, str | None]:
        base_name, multiplier = cls._get_product_base_name_and_multiplier(product_name)
        range_info = cls._RANGES.get(base_name)
        if range_info is None:
            return True, None

        min_price = range_info[0] * multiplier
        max_price = range_info[1] * multiplier

        if price < min_price:
            return False, f"Fiyat çok düşük: {price:.2f} TL (beklenen min: {min_price:.2f})"
        if price > max_price:
            return False, f"Fiyat çok yüksek: {price:.2f} TL (beklenen max: {max_price:.2f})"
        return True, None

    @classmethod
    def is_implausibly_low(cls, product_name: str, price: float) -> bool:
        """Puan/taksit kalıntısı (2 TL çeyrek gibi) kayda yazılmasın."""
        base_name, multiplier = cls._get_product_base_name_and_multiplier(product_name)
        range_info = cls._RANGES.get(base_name)
        if range_info is None:
            return price < 100
        min_price = range_info[0] * multiplier
        return price < (min_price * 0.5) # Eşik değerinin %50'sinin altındaysa kaydetme
