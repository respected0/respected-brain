"""The product's user settings: one schema behind `config`, `setup --set`, the installer and RPP `settings.*`.

Names live in the active vault's profile (the vault template, briefing and MCP tools read them there), integration
switches under `integrations`, everything else under `preferences`. A change that reaches outside the data folder
(AI client files, the scheduled task, the shortcut, the names written into them) is applied together with the
integrations in one transaction when the product is installed.
"""
from __future__ import annotations

import re
from pathlib import Path

from .core.config import ConfigStore, validate_config
from .core.errors import SelectionError

PROVIDERS = ["auto", "codex", "claude", "antigravity", "gemini", "cursor"]

FIELDS = (
    {"key": "user_name", "type": "string", "label": "Adın", "default": "", "max_length": 40,
     "help": "Asistan ve sabah özeti sana bu adla hitap eder."},
    {"key": "user_bio", "type": "string", "label": "Kısa tanıtım", "default": "", "max_length": 200,
     "help": "Kasa şablonunda seni tanıtan satıra yazılır."},
    {"key": "assistant_name", "type": "string", "label": "Asistanının adı", "default": "", "max_length": 40,
     "help": "Kasadaki asistan kimliği ve AI araçlarına verilen hafıza araçları bu adı kullanır (ör. Jarvis)."},
    {"key": "summary_provider", "type": "enum", "label": "Özetleyici AI", "default": "auto", "enum": PROVIDERS,
     "help": "Oturumları kasa notlarına özetleyen yerel AI aracı; auto kurulu olanı seçer."},
    {"key": "provider_fallback", "type": "boolean", "label": "Yedek özetleyici", "default": True,
     "help": "Seçilen AI aracı başarısız olursa diğer kurulu araçları dene."},
    {"key": "capture_mode", "type": "enum", "label": "Hafıza yakalama", "default": "auto", "enum": ["auto", "manual"],
     "help": "auto: oturumlar bitince kendiliğinden özetlenir. manual: yalnızca sen istediğinde işlenir."},
    {"key": "briefing_time", "type": "string", "label": "Sabah özeti saati", "default": "08:00", "max_length": 5,
     "help": "Zamanlanmış sabah özeti görevinin çalıştığı saat (SS:DD)."},
    {"key": "mcp_write", "type": "boolean", "label": "AI araçları not kaydedebilsin", "default": False,
     "help": "MCP ile yalnızca gelen kutusuna, geri alınabilir not kaydı."},
    {"key": "archive_transcripts", "type": "boolean", "label": "Oturum dökümlerini sakla", "default": False,
     "help": "Bağlam sıkıştırmasından sonra kurtarmak için gizli bilgileri ayıklanmış dökümler kasa dışında tutulur."},
    {"key": "transcript_retention_days", "type": "integer", "label": "Döküm saklama süresi (gün)", "default": 14,
     "min": 1, "max": 90, "help": "Saklanan oturum dökümlerinin silinme süresi."},
    {"key": "integrations.global", "type": "boolean", "label": "Oturumları hafızaya yakala", "default": False,
     "help": "Seçili AI araçlarına hafıza hook'ları, kuralları ve becerileri eklenir; diğer ayarların korunur."},
    {"key": "integrations.clients", "type": "string", "label": "Yakalanan AI araçları", "default": "", "max_length": 200,
     "help": "Virgülle ayrılmış liste (ör. claude,codex); boş: kurulu olanların hepsi."},
    {"key": "integrations.mcp", "type": "boolean", "label": "Hafıza MCP sunucusu", "default": False,
     "help": "AI araçları hafızayı MCP sunucusu olarak kullanabilir."},
    {"key": "integrations.mcp_clients", "type": "string", "label": "MCP izni olan AI araçları", "default": "",
     "max_length": 200, "help": "Virgülle ayrılmış liste; boş: yakalanan araçlarla aynı."},
    {"key": "integrations.schedule", "type": "boolean", "label": "Sabah özeti görevi", "default": False,
     "help": "İşletim sisteminin görev zamanlayıcısına günlük bir görev eklenir."},
    {"key": "integrations.shortcut", "type": "boolean", "label": "Masaüstü kısayolu", "default": False,
     "help": "Masaüstüne not kasasını Obsidian'da açan bir kısayol konur (obsidian:// bağlantısı; Obsidian'ın kasayı tanıması için kasayı bir kez Obsidian'da açmış olmanız gerekir)."},
)
SCHEMA = {field["key"]: field for field in FIELDS}

# profile key -> (vault settings name, the template placeholder an empty value is stored as)
_PROFILE = {"assistant_name": ("COMPANION", "Companion"), "user_name": ("USER_NAME", "User"), "user_bio": ("USER_BIO", "")}
_CLIENT_LISTS = ("integrations.clients", "integrations.mcp_clients")
_TIME = re.compile(r"([01]\d|2[0-3]):[0-5]\d\Z")


class SettingsError(Exception):
    """Invalid or unappliable settings; `errors` is a list of {key, message}."""

    def __init__(self, errors):
        super().__init__("; ".join(error["message"] for error in errors))
        self.errors = errors


def schema():
    return [{"secret": False, **field} for field in FIELDS]  # no Brain setting is a secret


def _clients(text):
    return [item.strip() for item in text.split(",") if item.strip()]


def _field_errors(field, value):
    key, kind = field["key"], field["type"]
    if kind == "boolean" and not isinstance(value, bool):
        return [{"key": key, "message": f"{key} true ya da false olmalı"}]
    if kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            return [{"key": key, "message": f"{key} tam sayı olmalı"}]
        if not field["min"] <= value <= field["max"]:
            return [{"key": key, "message": f"{key} {field['min']} ile {field['max']} arasında olmalı"}]
    if kind == "enum" and value not in field["enum"]:
        return [{"key": key, "message": f"{key} şunlardan biri olmalı: {', '.join(field['enum'])}"}]
    if kind == "string":
        if not isinstance(value, str):
            return [{"key": key, "message": f"{key} metin olmalı"}]
        if len(value) > field["max_length"]:
            return [{"key": key, "message": f"{key} en fazla {field['max_length']} karakter olabilir"}]
        if key == "briefing_time" and not _TIME.match(value):
            return [{"key": key, "message": "briefing_time SS:DD biçiminde olmalı (ör. 08:00)"}]
        if key in _CLIENT_LISTS:
            from .integrations.rendering import CLIENTS
            unknown = sorted(set(_clients(value)) - set(CLIENTS))
            if unknown:
                return [{"key": key, "message": f"Bilinmeyen AI aracı: {', '.join(unknown)} (geçerli: {', '.join(CLIENTS)})"}]
    return []


def field_errors(values):
    """Checks that need no stored configuration: known keys, types and ranges."""
    if not isinstance(values, dict):
        return [{"key": "", "message": "Ayarlar bir nesne olmalı"}]
    errors = []
    for key, value in values.items():
        field = SCHEMA.get(key)
        errors.extend([{"key": key, "message": f"Bilinmeyen ayar: {key}"}] if field is None else _field_errors(field, value))
    return errors


def write(document, values):
    """Apply already validated values to a configuration document (in place)."""
    for key, value in values.items():
        if key in _PROFILE:
            vault = (document.get("vaults") or {}).get(document.get("active_vault_id"))
            if vault is None:
                raise SelectionError("Bu ayar bir not kasasına aittir; önce kasa kurulmalı")
            name, placeholder = _PROFILE[key]
            vault.setdefault("settings", {})[name] = value.strip() or placeholder
        elif key in _CLIENT_LISTS:
            name = key.split(".", 1)[1]
            chosen = _clients(value)
            if chosen:
                document["integrations"][name] = sorted(chosen)
            else:
                document["integrations"].pop(name, None)
        elif key.startswith("integrations."):
            document["integrations"][key.split(".", 1)[1]] = value
        else:
            document["preferences"][key] = value


def current(document, key):
    field = SCHEMA[key]
    if key in _PROFILE:
        name, placeholder = _PROFILE[key]
        vault = (document.get("vaults") or {}).get(document.get("active_vault_id")) or {}
        value = (vault.get("settings") or {}).get(name, "")
        return "" if value == placeholder else value
    if key in _CLIENT_LISTS:
        return ",".join((document.get("integrations") or {}).get(key.split(".", 1)[1]) or [])
    if key.startswith("integrations."):
        return (document.get("integrations") or {}).get(key.split(".", 1)[1], field["default"])
    return (document.get("preferences") or {}).get(key, field["default"])


def readback(data_root: Path):
    document = ConfigStore(data_root).read()
    return {key: current(document, key) for key in SCHEMA}


def validate(data_root: Path, values):
    errors = field_errors(values)
    if errors:
        return errors
    try:
        document = ConfigStore(data_root).read()
        write(document, values)
        validate_config(document)
    except (SelectionError, OSError, ValueError) as error:
        return [{"key": "", "message": str(error)}]
    return []


def reaches_out(values):
    """True when the change must also rewrite files outside the data folder."""
    return any(key.startswith("integrations.") or key in _PROFILE or key == "briefing_time" for key in values)


def apply(data_root: Path, values):
    """Validate and store; when installed, outside-reaching changes go through the installation transaction."""
    errors = validate(data_root, values)
    if errors:
        raise SettingsError(errors)
    if reaches_out(values) and (data_root / "install-manifest.json").is_file():
        from .installation.reconfigure import reconfigure
        result = reconfigure(data_root, lambda document: write(document, values))
        if not result.success:
            raise SettingsError([{"key": "", "message": "Ayarlar uygulanamadı, değişiklik geri alındı: " + "; ".join(result.conflicts)}])
        return
    ConfigStore(data_root).update(lambda document: write(document, values))


def parse(assignment: str):
    """`key=value` from the command line or the installer, typed by the schema."""
    key, separator, text = assignment.partition("=")
    key = key.strip()
    field = SCHEMA.get(key)
    if not separator or field is None:
        raise SettingsError([{"key": key, "message": f"Bilinmeyen ayar ya da eksik '=': {assignment}"}])
    if field["type"] == "boolean":
        lowered = text.strip().lower()
        if lowered not in ("true", "false"):
            raise SettingsError([{"key": key, "message": f"{key} true ya da false olmalı"}])
        return key, lowered == "true"
    if field["type"] == "integer":
        try:
            return key, int(text)
        except ValueError:
            raise SettingsError([{"key": key, "message": f"{key} tam sayı olmalı"}]) from None
    return key, text


def profile_of(values):
    """The vault template values (USER_NAME, COMPANION, USER_BIO) the given settings carry."""
    return {name: values[key].strip() for key, (name, _) in _PROFILE.items() if isinstance(values.get(key), str) and values[key].strip()}
