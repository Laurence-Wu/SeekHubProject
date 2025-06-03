#!/usr/bin/env python3
"""
compare_titles.py – similarity metrics for two book titles (RapidFuzz only)

Outputs four scores (0 – 1):
  • Levenshtein ratio
  • Token‑sort ratio
  • Token‑set  ratio
  • Jaro‑Winkler similarity
"""

import re
import sys
import unicodedata
from typing import Dict

from rapidfuzz import fuzz, distance


# ---------- helpers ----------------------------------------------------------
def normalize(title: str) -> str:
    """
    Lower‑case, strip accents, remove punctuation, collapse spaces.

    This lets “Économie Politique” and “Economie‑politique” match cleanly.
    """
    title = unicodedata.normalize("NFKD", title) \
                       .encode("ascii", "ignore") \
                       .decode("ascii")
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s]", " ", title)   # keep letters, digits, spaces
    return re.sub(r"\s+", " ", title).strip()


def similarities(a: str, b: str) -> Dict[str, float]:
    """
    Return a dict of similarity metrics in the 0–1 range.
    """
    a_norm, b_norm = normalize(a), normalize(b)

    return {
        "levenshtein_ratio": distance.Levenshtein.normalized_similarity(
            a_norm, b_norm
        ),
        "token_sort_ratio": fuzz.token_sort_ratio(a_norm, b_norm) / 100.0,
        "token_set_ratio":  fuzz.token_set_ratio(a_norm, b_norm)  / 100.0,
        "jaro_winkler":     distance.JaroWinkler.similarity(a_norm, b_norm),
    }


# ---------- CLI --------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    title1, title2 = sys.argv[1], sys.argv[2]
    scores = similarities(title1, title2)

    print(f"\nComparing:\n  1. {title1}\n  2. {title2}\n")
    for name, value in scores.items():
        print(f"{name:18}: {value:.3f}")
