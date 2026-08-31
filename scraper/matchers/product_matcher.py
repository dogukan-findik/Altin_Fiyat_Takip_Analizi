import re


class ProductMatcher:
    """Pazaryeri ve kendi mağaza ürün başlıklarını Products tablosundaki
    ürün adlarına eşler.
    
    Öncelik sırası ve özel kurallar:
    1. Gremse / 2.5'luk: "gremse", "2.5 luk", "2 5 luk", "iki buçuklu" -> Gremse Altın
    2. Beşli / 5'lik: "beşli", "besli", "5'li", "5 lik" -> Beşli Altın
    3. Özel Ata İsimleri:
       - "ata tam" -> Tam Altın
       - "ata yarım", "ata yarim" -> Yarım Altın
       - "ata çeyrek", "ata ceyrek" -> Çeyrek Altın
    4. Reşat Altını: "reşat", "resat"
    5. Ata Altını (Ata Lira): "ata altın", "ata lira", "cumhuriyet"
    6. Standart Sarrafiye: Tam Altın, Yarım Altın, Çeyrek Altın
    7. Gram Altın ve 22 Ayar Bilezik (gram bazlı)

    Çoklu Adet Kuralı:
    - "1 Adet", "1 adet" vb. tekil üründür -> "Çeyrek Altın", "Tam Altın" vb.
    - "2 Adet", "3 Adet", "5 Adet", "10 Adet" vb. -> "3 Adet Çeyrek Altın", "5 Adet Tam Altın" vb.
    """

    GRAM_PRODUCTS = {"Gram Altın", "22 Ayar Bilezik"}

    @staticmethod
    def extract_quantity(text: str) -> int:
        """Başlıktaki adet sayısını çıkarır. Bulunamazsa 1 döner.
        Örnekler:
        - '3 Adet Ata Tam' -> 3
        - 'Agakulche Eski 2 Adet Ata Tam Altın' -> 2
        - 'Sarrafiye - 10 Adet Yeni Tarihli Çeyrek Altın' -> 10
        - '1 Adet Ata Çeyrek' -> 1
        - '5'li' -> 5 (eğer beşli altın veya adet ise)
        """
        lower = text.lower()

        # Eğer beşli altın veya 2.5'luk gremse ibaresiyse bunu adet paketi sayma (örn: REŞAT 5'li ALTIN -> Beşli Altın)
        if any(k in lower for k in ["beşli", "besli", "5'li altın", "5 li altın", "5'lik", "5 lik", "2.5 luk", "2,5 luk", "2 5 luk", "2.5'luk", "2.5luk"]):
            m_explicit = re.search(r"(\d+)\s*adet", lower)
            if m_explicit:
                return int(m_explicit.group(1))
            return 1

        # "X adet" / "X'li" deseni (Örn: "3 adet", "3'lü", "3'lu", "10 adet")
        m = re.search(r"(?:^|[^\d])(\d+)\s*(?:adet|'l[iü]|li)\b", lower)
        if m:
            qty = int(m.group(1))
            # Makul adet sınırı (örn 1 ile 100 arası)
            if 1 <= qty <= 100:
                return qty

        # Baştaki "X Adet" deseni
        m_start = re.match(r"^\s*(\d+)\s*adet\b", lower)
        if m_start:
            return int(m_start.group(1))

        return 1

    @classmethod
    def match(cls, title: str) -> str | None:
        """Ürün başlığından tam eşleşen ürün adını belirler.
        Çoklu adet varsa (örn: 3 Adet Çeyrek Altın), dinamik paket adı üretir."""
        lower = title.lower()

        # Bilezik dışındaki takıları filtrele
        jewelry_excludes = ["kolye", "halhal", "yüzük", "küpe", "bileklik", "çeyrekli", "zincir"]
        if any(ex in lower for ex in jewelry_excludes):
            return None

        qty = cls.extract_quantity(title)

        base_product: str | None = None

        # 1. GREMSE (2.5'luk) ALTIN
        if any(k in lower for k in ["gremse", "2.5 luk", "2,5 luk", "2 5 luk", "2.5'luk", "2.5luk", "iki buçuklu", "iki bucuklu", "2.5'lik"]):
            base_product = "Gremse Altın"

        # 2. BEŞLİ (5'lik) ALTIN
        elif any(k in lower for k in ["beşli", "besli", "5'lik", "5 lik", "reşat 5'li", "reşat 5 lik", "reşat 5'lik", "5'li altın", "5 li altın"]):
            base_product = "Beşli Altın"

        # 3. ÇEYREK ALTIN (Başlıkta 'ata lira çeyrek', 'ata çeyrek' olsa dahi Çeyrek Altın'dır)
        elif "çeyrek" in lower or "ceyrek" in lower:
            base_product = "Çeyrek Altın"

        # 4. YARIM ALTIN (Başlıkta 'ata lira yarım', 'ata yarım' olsa dahi Yarım Altın'dır)
        elif "yarım" in lower or "yarim" in lower:
            base_product = "Yarım Altın"

        # 5. TAM ALTIN ('ata tam', 'tam altın', 'tam lira' vb.)
        elif "ata tam" in lower or "tam altın" in lower or "tam altin" in lower or "tam lira" in lower or (
            "tam" in lower and any(k in lower for k in ["ata", "altın", "altin", "ziynet", "sarrafiye"])
        ):
            base_product = "Tam Altın"

        # 6. REŞAT ALTINI
        elif "reşat" in lower or "resat" in lower:
            base_product = "Reşat Altını"

        # 7. ATA ALTINI (Ata Lira / Cumhuriyet) - Çeyrek, Yarım, Tam içermeyen tekil Ata Lira
        elif any(k in lower for k in ["ata altın", "ata altin", "ata lira", "ata lirası"]) or "cumhuriyet" in lower:
            base_product = "Ata Altını"

        # 9. 22 AYAR BİLEZİK
        elif "bilezik" in lower:
            base_product = "22 Ayar Bilezik"

        # 10. GRAM ALTIN
        elif any(k in lower for k in ["külçe", "külce", "gram altın", "24 ayar", "gram 24"]):
            base_product = "Gram Altın"

        if base_product is None:
            return None

        # Çoklu Adet Yönetimi:
        # Gram Altın ve 22 Ayar Bilezik gramaj bazlıdır (örn. "5 Gram Altın", "10 Gram Bilezik").
        # Sarrafiye / Cumhuriyet altınları için qty > 1 ise "{qty} Adet {base_product}" oluşturulur.
        if base_product not in cls.GRAM_PRODUCTS:
            if base_product in ("Beşli Altın", "Gremse Altın"):
                m_explicit = re.search(r"(\d+)\s*adet", lower)
                if m_explicit and int(m_explicit.group(1)) > 1:
                    return f"{m_explicit.group(1)} Adet {base_product}"
                return base_product

            if qty > 1:
                return f"{qty} Adet {base_product}"
            return base_product

        return base_product

    @classmethod
    def is_gram_based(cls, product_name: str) -> bool:
        """Ürünün gram bazlı fiyat doğrulaması gerekip gerekmediğini kontrol eder."""
        return (
            product_name in cls.GRAM_PRODUCTS
            or "Gram Bilezik" in product_name
            or "Gram Altın" in product_name
        )
