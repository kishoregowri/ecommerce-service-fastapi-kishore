# shop/utils.py
import hashlib
from collections import defaultdict

def cart_signature(raw_items):
    """
    raw_items: iterable of dicts like {"sku": "care-1", "qty": 2}
    Normalize:
      - merge by sku (sum qty)
      - sort by sku asc
      - string "sku:qty" joined with '|'
      - sha256 hex digest
    Returns (normalization_string, sha256_hex)
    """
    merged = defaultdict(int)
    for it in raw_items:
        sku = str(it["sku"])
        qty = int(it["qty"])
        merged[sku] += qty
    parts = [f"{sku}:{merged[sku]}" for sku in sorted(merged)]
    norm = "|".join(parts)
    return norm, hashlib.sha256(norm.encode("utf-8")).hexdigest()
