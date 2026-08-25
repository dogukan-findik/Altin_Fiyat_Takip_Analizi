import re


class ProductMatcher:
    """N11 (ve benzeri pazaryeri) ürün başlıklarını Products tablosundaki
    ürün adlarına eşler. Öncelik sırası: özel cumhuriyet altınları
    (Reşat, Hamit, Ata) -> gram bazlı ürünler (Gram Altın, 22 Ayar
    Bilezik) -> standart cumhuriyet altınları (Tam, Yarım, Çeyrek).

    Bilezikler için özel mantık: Gram ağırlığına göre dinamik kategoriler
    oluşturulur (5 Gram Bilezik, 10 Gram Bilezik vb.) böylece model isimleri
    (burma, kibrit çöpü, hasır vb.) karşılaştırmayı etkilemez.

    Generic '22 Ayar Bilezik' ürününe asla düşülmez; gram çıkmazsa kayıt atlanır.
    """

    GRAM_PRODUCTS = {"Gram Altın", "22 Ayar Bilezik"}

    _RULES: list[tuple[str, list[str], list[str]]] = [
        ("Reşat Altını", ["reşat"], []),
        ("Ata Altını", ["ata altın", "ata lira", "ata altini"], []),

        # Sadece gerçek bilezikler. "22 ayar" tek başına bilezik sayılmaz.
        ("22 Ayar Bilezik", ["bilezik"],
         ["kolye", "halhal", "yüzük", "küpe", "bileklik", "14 ayar", "18 ayar"]),
        ("Gram Altın", ["külçe", "külce", "gram altın", "24 ayar", "gram 24", "22 ayar"],
         ["bilezik", "kolye", "yüzük", "küpe", "halhal", "bileklik"]),

        ("Tam Altın", ["tam altın", "tam altin", "tam lira", "cumhuriyet"],
         ["reşat", "ata", "çeyrek", "yarım", "yarim"]),
        ("Yarım Altın", ["yarım", "yarim"],
         ["reşat", "ata", "çeyrek", "tam"]),
        # "çeyrek" kelime sınırı ile; "çeyrekli bileklik" eşleşmez
        ("Çeyrek Altın", ["çeyrek"],
         ["reşat", "ata", "yarım", "yarim", "tam", "bileklik", "bilezik", "çeyrekli"]),
    ]

    @staticmethod
    def _has_keyword(text: str, keyword: str) -> bool:
        """Boşluklu ifadelerde alt string, tek kelimede kelime sınırı kullanır."""
        if " " in keyword:
            return keyword in text
        return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) is not None

    @classmethod
    def match(cls, title: str) -> str | None:
        """Ürün başlığından temel ürün tipini belirler.
        Bilezikler için daha sonra gram bazlı kategorilere ayrılacak."""
        lower = title.lower()

        for product_name, keywords, excludes in cls._RULES:
            if any(cls._has_keyword(lower, kw) for kw in keywords) and not any(
                cls._has_keyword(lower, ex) for ex in excludes
            ):
                return product_name

        return None

    @classmethod
    def is_gram_based(cls, product_name: str) -> bool:
        """Ürünün gram bazlı fiyat doğrulaması gerekip gerekmediğini kontrol eder.

        Gram Altın ve Bilezikler gram bilgisine ihtiyaç duyar:
        - '5 Gram Altın', '10 Gram Altın' vb.
        - '5 Gram Bilezik', '10 Gram Bilezik' vb.
        """
        return (
            product_name in cls.GRAM_PRODUCTS
            or "Gram Bilezik" in product_name
            or "Gram Altın" in product_name
        )
