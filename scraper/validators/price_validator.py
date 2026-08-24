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
        "Gram Altın": (500, 100000),  # 1g ~ 80g arası (toplam fiyat)
        "22 Ayar Bilezik": (3000, 150000),  # 5g ~ 100g arası (toplam fiyat)
        "Çeyrek Altın": (9000, 18000),
        "Yarım Altın": (18000, 36000),
        "Tam Altın": (36000, 72000),
        "Reşat Altını": (36000, 75000),
        "Ata Altını": (30000, 65000),
    }

    @classmethod
    def _get_product_base_name(cls, product_name: str) -> str:
        """'5 Gram Altın' → 'Gram Altın', '10 Gram Bilezik' → '22 Ayar Bilezik' gibi dönüştür."""
        if "Gram Altın" in product_name:
            return "Gram Altın"
        if "Gram Bilezik" in product_name:
            return "22 Ayar Bilezik"
        return product_name

    @classmethod
    def validate(cls, product_name: str, price: float) -> tuple[bool, str | None]:
        # Dinamik kategoriler için base name çıkar (5 Gram Altın → Gram Altın)
        base_name = cls._get_product_base_name(product_name)
        range_info = cls._RANGES.get(base_name)
        if range_info is None:
            return True, None

        min_price, max_price = range_info
        if price < min_price:
            return False, f"Fiyat çok düşük: {price:.2f} TL (beklenen min: {min_price})"
        if price > max_price:
            return False, f"Fiyat çok yüksek: {price:.2f} TL (beklenen max: {max_price})"
        return True, None
