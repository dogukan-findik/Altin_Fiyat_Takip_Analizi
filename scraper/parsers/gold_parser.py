import re

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
    # Sadece virgül ondalık ayracıysa -> "12450,75"
    elif ',' in cleaned and '.' not in cleaned:
        cleaned = cleaned.replace(',', '.')
    # Aksi halde zaten "12450.75" formatında kabul et, dokunma

    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None

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
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(gr|gram|g)\b', text.lower())
    if not match:
        return None
    return float(match.group(1).replace(',', '.'))
