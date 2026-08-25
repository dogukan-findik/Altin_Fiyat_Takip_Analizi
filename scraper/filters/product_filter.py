import re


class ProductFilter:
    """N11 ürün başlıklarında karşılaştırmaya uygun olmayan ürünleri
    (kendi markamız, çoklu paketler, işlenmiş takılar, ikinci el/hasarlı)
    ayıklar. Reddedilenler DB'ye hiç yazılmaz, sadece loglanır.
    
    Gelişmiş filtreleme:
    - Çoklu ürün paketleri (2 adet, 3'lü vb.)
    - İşlenmiş/süslü takılar (taşlı, mineli vb.)
    - Bilezik dışındaki takılar
    - İkinci el/hasarlı ürünler
    - Sabit bileziğe geçmeli ürünler (geçme altın)
    """

    _EXCLUDE_STRINGS = [
        "ahlatcı", "ahlatci", "Ahlatcı Kuyumculuk", "ahlatci kuyumculuk",
        # Çoklu paketler
        "takım", "set", "çift", "paket", "kombin",
        # İşlenmiş takılar (bilezik hariç)
        "kolye", "küpe", "yüzük", "halhal", "broş", "iğne", "kol düğmesi",
        "zincir", "koleksiyon", "şans kolyesi", "gerdanlık",
        "bileklik", "çeyrekli",
        # Süsleme terimleri
        "taşlı", "pırlanta", "elmas", "zümrüt", "safir", "yakut",
        "mineli", "mine", "swarovski", "kristal",
        "özel tasarım", "el yapımı", "işlemeli",
        # Durumsal problemler
        "ikinci el", "antika", "eski tarih", "nostalji",
        "hasarlı", "kusurlu", "kullanılmış", "ikinci kalite",
        # Sabit/geçme ürünler
        "geçme", "geçmeli", "sabit", "sallantılı",
        # Diğer
        "replika", "kopya", "model", "taklit",
    ]

    _EXCLUDE_PATTERNS = [
        r"\d+\s*adet",           # "2 adet", "5 adet"
        r"\d+['']l[iü]",         # "3'lü", "5'li"
        r"\d+\s*parça",          # "3 parça"
        r"\bx\d+\b",             # "x2", "x5"
        r"\d+\s*li\s+set",       # "2 li set"
    ]

    @classmethod
    def should_exclude(cls, title: str) -> tuple[bool, str | None]:
        """Ürün başlığını filtrelerden geçirir. 
        Filtreye takılan ürün için (True, sebep) döner."""
        lower = title.lower()

        for term in cls._EXCLUDE_STRINGS:
            if term in lower:
                return True, f"'{term}' içeriyor"

        for pattern in cls._EXCLUDE_PATTERNS:
            if re.search(pattern, lower):
                return True, f"desen eşleşti: {pattern}"

        return False, None
