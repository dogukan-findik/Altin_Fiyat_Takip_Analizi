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
        # İşlenmiş takılar (bilezik hariç)
        "kolye", "küpe", "yüzük", "halhal", "broş", "iğne", "kol düğmesi",
        "zincir", "koleksiyon", "şans kolyesi", "gerdanlık",
        "bileklik", "çeyrekli",
        # Süsleme terimleri
        "taşlı", "pırlanta", "elmas", "zümrüt", "safir", "yakut",
        "mineli", "mine", "swarovski", "kristal",
        "özel tasarım", "el yapımı", "işlemeli",
        # Durumsal problemler (NOT: 'eski tarih' izin veriliyor - fiyatlar yeni tarihle aynı)
        "ikinci el", "antika", "nostalji",
        "hasarlı", "kusurlu", "kullanılmış", "ikinci kalite",
        # Sabit/geçme ürünler
        "geçme", "geçmeli", "sabit", "sallantılı",
        # Diğer
        "replika", "kopya", "model", "taklit",
    ]

    _EXCLUDE_PATTERNS = [
        r"\d+\s*parça\s+tak[ıi]", # takı setleri
        r"tak[ıi]\s+set[iİ]",
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
