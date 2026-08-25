import re

# Kart metninden aday fiyatlar. En spesifik (binlik + kuruş) önce.
_PRICE_FINDERS = [
    re.compile(r"\d{1,3}(?:\.\d{3})+,\d{1,2}"),  # 12.874,33
    re.compile(r"\d{4,},\d{1,2}"),               # 12874,33
    re.compile(r"\d{1,3}(?:\.\d{3})+"),           # 12.874
    re.compile(r"\d+,\d{2}"),                     # 2,60 veya 874,33
    re.compile(r"\d+\.\d{2}"),                     # 12874.33
]

# Puan / taksit / kargo gibi küçük sayıların asıl fiyat sanılmaması
_MIN_PLAUSIBLE_LISTING_PRICE = 100.0


def parse_price(raw_price: str) -> float | None:
    """'12.450,75 TL', '12450.75', '₺12.450,75' gibi farklı formatlardan
    ondalık fiyat çıkarır. Parse edilemeyen değerler için None döner
    (asla tahmini/uydurma bir sayı üretmez — çağıran taraf None'ı
    'bu kaydı atla' sinyali olarak yorumlamalı)."""
    if not raw_price:
        return None

    cleaned = re.sub(r'[^\d,.\-]', '', raw_price.strip())
    if not cleaned:
        return None

    # Türkçe format: binlik nokta, ondalık virgül -> "12.450,75"
    if re.match(r'^\d{1,3}(\.\d{3})*,\d+$', cleaned):
        cleaned = cleaned.replace('.', '').replace(',', '.')
    # Binlik nokta, kuruş yok -> "12.874"
    elif re.match(r'^\d{1,3}(\.\d{3})+$', cleaned):
        cleaned = cleaned.replace('.', '')
    # Sadece virgül ondalık ayracıysa -> "12450,75"
    elif ',' in cleaned and '.' not in cleaned:
        cleaned = cleaned.replace(',', '.')
    # Aksi halde zaten "12450.75" formatında kabul et, dokunma

    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def extract_prices_from_text(text: str) -> list[float]:
    """Bir metindeki tüm fiyat adaylarını (soldan sağa, örtüşmeyen) çıkarır."""
    if not text:
        return []

    found: list[float] = []
    occupied: list[tuple[int, int]] = []

    for pattern in _PRICE_FINDERS:
        for match in pattern.finditer(text):
            span = match.span()
            if any(span[0] >= s[0] and span[1] <= s[1] for s in occupied):
                continue
            price = parse_price(match.group(0))
            if price is None:
                continue
            found.append(price)
            occupied.append(span)

    return found


def resolve_listing_price_text(primary_text: str, extra_text: str = "") -> str:
    """N11 kartında seçilen fiyat düğümü puan/taksit (ör. 2,60) olabilir.
    Önce birincil metin makul bir altın fiyatıysa onu kullanır; değilse
    kartın geri kalanındaki en yüksek makul fiyatı seçer."""
    primary = parse_price(primary_text) if primary_text else None
    if primary is not None and primary >= _MIN_PLAUSIBLE_LISTING_PRICE:
        return primary_text

    combined = " ".join(part for part in (primary_text, extra_text) if part)
    plausible = [p for p in extract_prices_from_text(combined) if p >= _MIN_PLAUSIBLE_LISTING_PRICE]
    if plausible:
        return f"{max(plausible):.2f}"

    return primary_text or ""

def is_in_stock(raw_availability_text: str | None) -> bool:
    """Stok durumu metnini yorumlar. Belirsizse (site stok bilgisi
    vermiyorsa) varsayılan olarak 'stokta' kabul edilir — çünkü çoğu
    site sadece 'tükendi' durumunu açıkça belirtir."""
    if not raw_availability_text:
        return True

    out_of_stock_keywords = ['tükendi', 'stokta yok', 'stok yok', 'satışta değil']
    text = raw_availability_text.lower()
    return not any(kw in text for kw in out_of_stock_keywords)

def extract_gram_weight(text: str) -> float | None:
    """Başlıktan gramaj çıkarır: '10 Gram 22 Ayar...', '5 Gr 24 Ayar...' gibi.
    Bulunamazsa None döner — çağıran taraf bunu 'gram bazlı normalize
    edilemedi, bu kaydı atla' sinyali olarak yorumlamalı."""
    # Önce tam sayı gram'ı ara (en yaygın format)
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(gr|gram|g)\b', text.lower())
    if match:
        return float(match.group(1).replace(',', '.'))
    
    # Alternatif formatlar: "5gr", "10gram" (boşluksuz)
    match = re.search(r'(\d+(?:[.,]\d+)?)(gr|gram|g)\b', text.lower())
    if match:
        return float(match.group(1).replace(',', '.'))
    
    return None

def extract_bracelet_category(text: str) -> str | None:
    """Bilezik ürünlerinden gram ağırlığını çıkarıp kategori oluşturur.
    Örnek: '5 Gram 22 Ayar Bilezik' -> '5 Gram Bilezik'
           '10 Gr Burma Bilezik' -> '10 Gram Bilezik'
           '7.5 Gram Kibrit Çöpü' -> '7.5 Gram Bilezik'
    
    Bu sayede aynı gramajdaki bilezikler model isimlerinden (burma, kibrit çöpü, 
    hasır vb.) bağımsız olarak karşılaştırılabilir."""
    
    gram = extract_gram_weight(text)
    if gram is None:
        return None
    
    # Tam sayı gramsa ondalık kısım olmadan, değilse ondalıklı göster
    if gram == int(gram):
        return f"{int(gram)} Gram Bilezik"
    else:
        return f"{gram} Gram Bilezik"

def categorize_gold_product(text: str, base_product_name: str) -> str | None:
    """Ürün başlığından ve temel ürün tipinden gram bazlı kategori oluşturur.
    
    Bilezikler için: gram ağırlığına göre ayrı kategoriler oluşturur.
    Gram Altın için: gram ağırlığına göre ayrı kategoriler oluşturur.
    Diğer ürünler için: temel ürün adını döndürür.
    
    Örnekler:
    - '5 Gram 22 Ayar Bilezik' + '22 Ayar Bilezik' -> '5 Gram Bilezik'
    - '10 Gram Külçe Altın' + 'Gram Altın' -> '10 Gram Altın'
    - '5 Gram 24 Ayar' + 'Gram Altın' -> '5 Gram Altın'
    - 'Tam Altın' + 'Tam Altın' -> 'Tam Altın'
    """
    
    if "bilezik" in base_product_name.lower():
        # Generic '22 Ayar Bilezik'e düşme: gram yoksa None (kayıt atlanır)
        return extract_bracelet_category(text)
    
    # Gram Altın için de gram bazlı kategori oluştur
    if "gram altın" in base_product_name.lower():
        gram = extract_gram_weight(text)
        if gram is not None:
            if gram == int(gram):
                return f"{int(gram)} Gram Altın"
            else:
                return f"{gram} Gram Altın"
    
    return base_product_name
