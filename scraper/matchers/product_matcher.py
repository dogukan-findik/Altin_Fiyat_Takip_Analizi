class ProductMatcher:
    """N11 (ve benzeri pazaryeri) ürün başlıklarını Products tablosundaki
    ürün adlarına eşler. Öncelik sırası: özel cumhuriyet altınları
    (Reşat, Hamit, Ata) -> gram bazlı ürünler (Gram Altın, 22 Ayar
    Bilezik) -> standart cumhuriyet altınları (Tam, Yarım, Çeyrek).
    
    Bilezikler için özel mantık: Gram ağırlığına göre dinamik kategoriler
    oluşturulur (5 Gram Bilezik, 10 Gram Bilezik vb.) böylece model isimleri
    (burma, kibrit çöpü, hasır vb.) karşılaştırmayı etkilemez."""

    # Bu ürünlerde toplam fiyat değil, gram başına fiyat kaydedilir.
    # Bilezikler de gram bazlı ama dinamik kategorilere sahip
    GRAM_PRODUCTS = {"Gram Altın", "22 Ayar Bilezik"}

    _RULES: list[tuple[str, list[str], list[str]]] = [
        # Özel cumhuriyet altınları
        ("Reşat Altını", ["reşat"], []),
        ("Ata Altını", ["ata altın", "ata lira", "ata altini"], []),

        # Gram bazlı ürünler
        ("22 Ayar Bilezik", ["bilezik", "22 ayar"], ["kolye", "halhal", "yüzük", "küpe", "14 ayar", "18 ayar"]),
        ("Gram Altın", ["külçe", "külce", "gram altın", "24 ayar", "gram 24"],
         ["bilezik", "kolye", "yüzük", "küpe", "halhal", "22 ayar"]),

        # Standart cumhuriyet altınları
        ("Tam Altın", ["tam altın", "tam altin", "tam lira", "cumhuriyet"],
         ["reşat", "ata", "çeyrek", "yarım", "yarim"]),
        ("Yarım Altın", ["yarım", "yarim"],
         ["reşat", "ata", "çeyrek", "tam"]),
        ("Çeyrek Altın", ["çeyrek"],
         ["reşat", "ata", "yarım", "yarim", "tam"]),
    ]

    @classmethod
    def match(cls, title: str) -> str | None:
        """Ürün başlığından temel ürün tipini belirler.
        Bilezikler için daha sonra gram bazlı kategorilere ayrılacak."""
        lower = title.lower()

        for product_name, keywords, excludes in cls._RULES:
            if any(kw in lower for kw in keywords) and not any(ex in lower for ex in excludes):
                return product_name

        return None
    
    @classmethod
    def is_gram_based(cls, product_name: str) -> bool:
        """Ürünün gram bazlı fiyat doğrulaması gerekip gerekmediğini kontrol eder.
        
        Gram Altın ve Bilezikler gram bilgisine ihtiyaç duyar:
        - '5 Gram Altın', '10 Gram Altın' vb.
        - '5 Gram Bilezik', '10 Gram Bilezik' vb.
        """
        return product_name in cls.GRAM_PRODUCTS or "Gram Bilezik" in product_name or "Gram Altın" in product_name
