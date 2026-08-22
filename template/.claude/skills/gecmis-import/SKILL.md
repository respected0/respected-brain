---
name: gecmis-import
description: Eski sohbet geçmişini (ChatGPT, Claude, Gemini Takeout dışa aktarımları) vault'un günlük log formatına çevirip derleyicinin sindirmesi için daily/ altına yazar. "geçmiş import", "geçmişimi aktar", "takeout", "chatgpt geçmişi", "eski sohbetlerimi beyne yükle" dendiğinde kullan.
---

# Geçmiş İçe Aktarımı

Eski sohbet arşivini beynin normal hattına sokar: dışa aktarım dosyası okunur, aylara bölünür,
`daily/import-YYYY-MM.md` dosyaları olarak yazılır. Oradan sonrası normal akış, her akşam
çalışan derleyici bu logları da sindirip `knowledge/` altına makale çıkarır.

Her şey yerelde kalır. Dışa aktarım dosyası hiçbir yere yüklenmez, hiçbir servise gönderilmez.

## Adımlar

1. Kullanıcıya dışa aktarım dosyasının yolunu sor. Tahmin etme, sorup bekle.
   - ChatGPT: dışa aktarım zip'i içindeki `conversations.json`. Zip hâlâ açılmadıysa kullanıcıdan
     açmasını iste veya `unzip` ile aç, sonra `conversations.json` yolunu kullan.
   - Claude: dışa aktarım içindeki `conversations.json` (farklı şema, aşağıda ayrı kod var).
   - Gemini: Google Takeout içindeki `My Activity/Gemini Apps/MyActivity.json`.
2. Dosya boyutunu ölç: `ls -lh <yol>` veya `wc -c < <yol>`.
   50 MB üstündeyse betik kendiliğinden **son 12 ayı** alır. Bunu kullanıcıya söyle: geri kalan
   arşiv duruyor, istenirse ikinci turda daha eski aralık alınabilir.
3. Aşağıdaki uygun betiği `.claude/scripts/.state/import-chatgpt.py` (veya `-claude.py`) olarak
   yaz, sonra çalıştır. `.state/` klasörü git dışıdır, geçici dosya orada kalır.
4. Betiğin özet çıktısını kullanıcıya aynen aktar: kaç sohbet, kaç ay dosyası, kaç karakter.
5. Derleme planını anlat (aşağıdaki "Sonra ne olur" bölümü).

## ChatGPT betiği

ChatGPT dışa aktarımında her sohbet bir **mapping ağacıdır**: `mapping` sözlüğünde her anahtar
bir düğüm kimliği, değeri `{"message": ..., "parent": ..., "children": [...]}`. Kök düğümün
`parent` alanı boştur ve genelde mesajı yoktur. Konuşmayı düz metne çevirmek için kökten
başlayıp `children` zincirini gezmek gerekir. Dallanma varsa (kullanıcı bir mesajı düzenlemişse)
tüm dallar sırayla yazılır, bu kayıp yaşamamak için bilinçli bir tercihtir.

```python
#!/usr/bin/env python3
"""Flatten a ChatGPT conversations.json export into vault daily logs."""

import json
import os
import sys
import time

MAX_EXPORT_BYTES = 50 * 1024 * 1024   # above this, keep only the recent window
RECENT_MONTHS = 12
MAX_MSG_CHARS = 4000
MAX_CONV_CHARS = 8000
MAX_FILE_CHARS = 200000
OUT_DIR = "daily"


def load_export(path):
    if os.path.isdir(path):
        path = os.path.join(path, "conversations.json")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):                      # some exports wrap the list
        data = data.get("conversations", [])
    return path, data


def message_text(msg):
    """Return plain text for a user/assistant message, or None to skip it."""
    if not isinstance(msg, dict):
        return None, None
    author = msg.get("author") or {}
    role = author.get("role")
    if role not in ("user", "assistant"):           # system and tool are dropped
        return None, None
    meta = msg.get("metadata") or {}
    if meta.get("is_visually_hidden_from_conversation"):
        return None, None
    content = msg.get("content") or {}
    if content.get("content_type") not in ("text", "multimodal_text", None):
        return None, None
    parts = []
    for part in content.get("parts") or []:
        if isinstance(part, str) and part.strip():
            parts.append(part.strip())
        elif isinstance(part, dict) and isinstance(part.get("text"), str):
            if part["text"].strip():
                parts.append(part["text"].strip())
    if not parts:
        return None, None
    text = "\n".join(parts)
    if len(text) > MAX_MSG_CHARS:
        text = text[:MAX_MSG_CHARS] + " [kısaltıldı]"
    return role, text


def walk_mapping(mapping):
    """Depth first walk from every root node, following children in order."""
    roots = [nid for nid, node in mapping.items()
             if isinstance(node, dict) and not node.get("parent")]
    if not roots:                                   # damaged export, take any node
        roots = list(mapping.keys())[:1]
    turns = []
    seen = set()
    for root in roots:
        stack = [root]
        while stack:
            nid = stack.pop()
            if nid in seen:
                continue
            seen.add(nid)
            node = mapping.get(nid)
            if not isinstance(node, dict):
                continue
            role, text = message_text(node.get("message"))
            if role:
                turns.append((role, text))
            children = node.get("children") or []
            for child in reversed(children):        # reversed so first child pops first
                stack.append(child)
    return turns


def conv_time(conv, mapping):
    ts = conv.get("create_time") or conv.get("update_time")
    if isinstance(ts, (int, float)) and ts > 0:
        return ts
    for node in mapping.values():
        msg = (node or {}).get("message") or {}
        mts = msg.get("create_time")
        if isinstance(mts, (int, float)) and mts > 0:
            return mts
    return time.time()


def main():
    if len(sys.argv) < 2:
        print("kullanım: python3 import-chatgpt.py <conversations.json>")
        return 1
    path, convs = load_export(sys.argv[1])
    size = os.path.getsize(path)
    cutoff = 0.0
    if size > MAX_EXPORT_BYTES:
        cutoff = time.time() - RECENT_MONTHS * 30 * 24 * 3600
        print("büyük arşiv (%.1f MB), son %d ay alınıyor" % (size / 1048576.0, RECENT_MONTHS))

    months = {}
    used = skipped = 0
    for conv in convs:
        if not isinstance(conv, dict):
            continue
        mapping = conv.get("mapping") or {}
        if not isinstance(mapping, dict) or not mapping:
            continue
        ts = conv_time(conv, mapping)
        if ts < cutoff:
            skipped += 1
            continue
        turns = walk_mapping(mapping)
        if not turns:
            skipped += 1
            continue
        stamp = time.localtime(ts)
        month = time.strftime("%Y-%m", stamp)
        title = (conv.get("title") or "başlık yok").replace("\n", " ").strip()
        head = "### Oturum (%s) ChatGPT: %s\n" % (
            time.strftime("%Y-%m-%d %H:%M", stamp), title)
        body = []
        total = 0
        for role, text in turns:
            label = "**User:**" if role == "user" else "**Assistant:**"
            chunk = "%s %s\n" % (label, text)
            if total + len(chunk) > MAX_CONV_CHARS:
                body.append("[konuşmanın devamı kısaltıldı]\n")
                break
            body.append(chunk)
            total += len(chunk)
        months.setdefault(month, []).append(head + "\n" + "\n".join(body))
        used += 1

    os.makedirs(OUT_DIR, exist_ok=True)
    written = []
    for month in sorted(months):
        out = os.path.join(OUT_DIR, "import-%s.md" % month)
        header = ("# Günlük Log: %s (içe aktarım)\n\n"
                  "Kaynak: ChatGPT dışa aktarımı. Bu dosya makine tarafından yazıldı.\n\n"
                  "## Oturumlar\n\n" % month)
        chunks = []
        total = len(header)
        cut = False
        for block in months[month]:
            if total + len(block) > MAX_FILE_CHARS:
                cut = True
                break
            chunks.append(block)
            total += len(block)
        text = header + "\n".join(chunks)
        if cut:
            text += "\n[bu ay dosya sınırı nedeniyle kısaltıldı]\n"
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        written.append((out, len(months[month]), len(text)))

    print("alınan sohbet: %d, atlanan: %d" % (used, skipped))
    for out, count, chars in written:
        print("  %s  %d sohbet  %d karakter" % (out, count, chars))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Claude betiği

Claude dışa aktarımının şeması düzdür, ağaç yoktur: her sohbet `chat_messages` listesi taşır.
Yukarıdaki betiğin `load_export`, ay gruplama ve yazma kısımlarını aynen kullan, sadece sohbet
çözümlemesini bununla değiştir:

```python
def claude_turns(conv):
    """Flatten one Claude export conversation into (role, text) pairs."""
    turns = []
    for msg in conv.get("chat_messages") or []:
        sender = msg.get("sender")
        role = {"human": "user", "assistant": "assistant"}.get(sender)
        if not role:
            continue
        parts = []
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                if isinstance(block.get("text"), str) and block["text"].strip():
                    parts.append(block["text"].strip())
        if not parts and isinstance(msg.get("text"), str) and msg["text"].strip():
            parts.append(msg["text"].strip())
        if parts:
            turns.append((role, "\n".join(parts)))
    return turns
```

Zaman damgası için `conv.get("created_at")` ISO metnidir:
`time.mktime(time.strptime(conv["created_at"][:19], "%Y-%m-%dT%H:%M:%S"))`.

## Gemini Takeout

Takeout arşivinde `My Activity/Gemini Apps/` klasörü var. JSON seçtiysen `MyActivity.json` bir
kayıt listesidir: `title` alanı genelde `Prompted <metin>` biçiminde, `time` alanı ISO damgadır,
yanıt varsa kayıtta ayrı bir alanda tutulur. Bu format sohbet bütünlüğünü korumaz, her kayıt tek
bir istemdir. O yüzden Gemini içe aktarımını **istem günlüğü** gibi yaz: aynı günün kayıtlarını
tek bir `### Oturum (YYYY-MM-DD) Gemini` bloğunda topla, her kaydı `**User:**` satırı yap.
Takeout'u HTML olarak aldıysan kullanıcıdan JSON formatında yeniden indirmesini iste, HTML
ayrıştırmak kırılgan ve gereksiz.

## Sonra ne olur

İçe aktarım bittiğinde kullanıcıya dürüst tabloyu ver:

- `daily/import-*.md` dosyaları yazıldı, derleyici bunları normal günlük loglar gibi görüyor.
- Derleyici akşamları **bir tur** çalışır ve her turda değişen logları işler, yani büyük bir
  arşiv birkaç akşama yayılır. Bu yavaşlık kasıtlı: abonelik limitini tek gecede yakmamak için.
- Beklemek istemiyorsa elle sürebilir: `python3 .claude/scripts/compile.py --dry-run` ile ne
  işleneceğini gör, sonra `python3 .claude/scripts/compile.py` ile bir tur çalıştır. Her tur
  aboneliğin günlük payından bir miktar tüketir, arka arkaya çalıştırmak limiti tüketebilir.
- 12 aydan eski arşiv atlandıysa bunu söyle ve ne zaman ikinci tur yapılacağını sor.

Son adım: `beyin-doktor` çalıştırmayı öner, derleme durumu satırından ilerlemeyi takip eder.
