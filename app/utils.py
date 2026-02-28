from __future__ import annotations

import re
import random
import string
import uuid
from datetime import datetime, timezone
from typing import Optional


# Basic Cyrillic (Russian + Kazakh) → Latin transliteration map
_TRANSLIT_MAP: dict = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
    # Kazakh-specific
    "ә": "a", "ғ": "gh", "қ": "q", "ң": "ng", "ө": "o",
    "ұ": "u", "ү": "u", "һ": "h", "і": "i",
}


def _transliterate(text: str) -> str:
    result = []
    for ch in text.lower():
        result.append(_TRANSLIT_MAP.get(ch, ch))
    return "".join(result)


def _random_suffix(length: int = 4) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def build_base_slug(organizer_name: str, category_slug: str, year: Optional[int] = None) -> str:
    """Generate a URL-safe slug from organizer name, category and year."""
    if year is None:
        year = datetime.now(timezone.utc).year
    translit = _transliterate(organizer_name)
    clean = re.sub(r"[^a-z0-9]+", "-", translit).strip("-")
    clean = clean[:30]
    return f"{clean}-{category_slug}-{year}"


def make_unique_slug(base_slug: str) -> str:
    """Append a random 4-char suffix to resolve slug collisions."""
    return f"{base_slug}-{_random_suffix()}"


def new_uuid() -> str:
    return str(uuid.uuid4())
