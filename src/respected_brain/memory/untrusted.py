"""Keep directive-shaped lines in external text visibly inert while quoting them to a model."""
from __future__ import annotations

import re

DIRECTIVE_SHAPED = re.compile(
    r"(?im)^[ \t]*(?:"
    r"UNTRUSTED[_ -]?DIRECTIVE|DIRECTIVE|INSTRUCTION|SYSTEM|ASSISTANT|"
    r"TAL[İI]MAT|KOMUT|IGNORE\s+(?:ALL|ANY|PREVIOUS|PRIOR)\b|"
    r"(?:ÖNCEKİ|TÜM)\s+(?:TAL[İI]MATLARI|KURALLARI)\s+(?:YOKSAY|UNUT)\b"
    r")\s*[:：]?"
)
INERT_PREFIX = "[UNTRUSTED_DATA] "


def inert(text: str) -> str:
    """Prefix directive-shaped lines; the original words stay readable as evidence, not as an order."""
    return DIRECTIVE_SHAPED.sub(lambda match: INERT_PREFIX + match.group(0).lstrip(), text)
