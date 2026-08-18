import re
import unicodedata
from difflib import SequenceMatcher

def normalize_product_name(name: str) -> str:
    """'10Gr Gram Altın 22 Ayar' -> '10gr_gram_altin_22_ayar'"""
    name = name.lower()
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('utf-8')

    # Gramaj standardizasyonu: "10gr", "10 gr", "10gram" -> "10gr"
    name = re.sub(r'(\d+)\s*(gr|gram|g)\b', r'\1gr', name)
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name

def calculate_similarity(name1: str, name2: str) -> float:
    """0-100 arası benzerlik skoru — C# tarafındaki Levenshtein tabanlı
    CalculateSimilarity ile aynı amaçlı kullanılır,  buradaki algoritma farklı
    (SequenceMatcher) kullanıyoruz ama ikisi de aynı normalize edilmiş string üzerinden
    çalıştığı için pratik sonuçlar tutarlı kalır."""
    n1 = normalize_product_name(name1)
    n2 = normalize_product_name(name2)
    return round(SequenceMatcher(None, n1, n2).ratio() * 100, 2)
