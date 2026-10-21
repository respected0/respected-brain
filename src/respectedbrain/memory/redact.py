"""Secret redaction for session text that leaves the user's machine (summariser prompt) or is stored (summaries, archives).

Best effort and conservative: a pattern list for well-known credential shapes plus `name = value` pairs whose name says
secret. It cannot find every secret (a password in prose stays), which is why transcript archives are opt-in and
the summary is redacted again before it is written.
"""
from __future__ import annotations

import re

_NAME = r"(?:api[_-]?key|apikey|secret[_-]?key|client[_-]?secret|secret|token|access[_-]?token|auth[_-]?token|refresh[_-]?token|password|passwd|pwd|parola|şifre|sifre|authorization|private[_-]?key)"

_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("private-key", re.compile(r"-----BEGIN (?:[A-Z0-9_ -]+ )?PRIVATE KEY-----.*?(?:-----END (?:[A-Z0-9_ -]+ )?PRIVATE KEY-----|\Z)", re.S), "[REDACTED:private-key]"),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), "[REDACTED:jwt]"),
    ("bearer", re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{16,}"), r"\1 [REDACTED:credential]"),
    ("provider-token", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}"), "[REDACTED:provider-token]"),
    ("provider-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{16,}\b"), "[REDACTED:provider-token]"),
    ("provider-token", re.compile(r"\b(?:hf_[A-Za-z0-9]{20,}|xox[baprs]-[0-9A-Za-z-]{10,}|AIza[0-9A-Za-z_-]{30,}|npm_[A-Za-z0-9]{30,})\b"), "[REDACTED:provider-token]"),
    ("cloud-credential", re.compile(r"\b(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b"), "[REDACTED:cloud-credential]"),
    ("url-credential", re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://[^\s/:@\"']+:)[^\s/@\"']{3,}(@)"), r"\1[REDACTED:password]\2"),
    # name = value / "name": "value" / NAME=value  (JSON and .env shapes); the value must look like a credential, not a word
    ("named-secret", re.compile(r"(?i)((?:\"|')?[\w.-]*" + _NAME + r"[\w.-]*(?:\"|')?\s*[:=]\s*)(\"|')?([^\s\"',;}{\\]{8,})"), r"\1\2[REDACTED:secret]"),
)


def redact(text: str) -> str:
    for _category, pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text

