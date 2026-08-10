#!/usr/bin/env python3
"""Fill missing i18n keys from en.json into sibling locale files (JSON only).

Does not modify Vue/business code. Preserves existing translations and extras.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from deep_translator import GoogleTranslator

ROOT = Path("/Users/mac/Code_Start/Aislos")

TARGETS = [
    ROOT / "Ainerwise/frontend-pc/i18n",
    ROOT / "Ainerwise/frontend-h5/i18n",
    ROOT / "Ainerwise/frontend-admin/i18n",
    ROOT / "Ainerwise/modules/procurement/h5/locales",
    ROOT / "Ainerwise/modules/procurement/pc/locales",
    ROOT / "CebuProjects/h5-frontend/locales",
    ROOT / "CebuProjects/pc-frontend/locales",
]

# GoogleTranslator language codes
LANG_MAP = {
    "zh": "zh-CN",
    "sr": "sr",
    "pl": "pl",
    "ar": "ar",
    "es": "es",
    "id": "id",
    "ja": "ja",
    "ko": "ko",
    "th": "th",
    "tl": "tl",
    "vi": "vi",
    "fil": "tl",
    "de": "de",
    "ro": "ro",
    "bs": "bs",
}

# Domain glossary: EN phrase -> {lang: translation}
GLOSSARY: dict[str, dict[str, str]] = {
    "Most Offers": {
        "zh": "最多报价",
        "sr": "Najviše ponuda",
        "pl": "Najwięcej ofert",
        "ja": "オファー最多",
        "ko": "제안 최다",
        "th": "ข้อเสนอมากที่สุด",
        "vi": "Nhiều báo giá nhất",
        "id": "Penawaran terbanyak",
        "es": "Más ofertas",
        "ar": "أكثر العروض",
        "tl": "Pinakamaraming alok",
        "fil": "Pinakamaraming alok",
    },
    "Deadline": {
        "zh": "截止日期",
        "sr": "Rok",
        "pl": "Termin",
        "ja": "締め切り",
        "ko": "마감일",
        "th": "กำหนดส่ง",
        "vi": "Hạn chót",
        "id": "Tenggat waktu",
        "es": "Fecha límite",
        "ar": "الموعد النهائي",
        "tl": "Deadline",
        "fil": "Deadline",
    },
    "Rank": {
        "zh": "排名",
        "sr": "Rang",
        "pl": "Ranking",
        "ja": "ランク",
        "ko": "순위",
        "th": "อันดับ",
        "vi": "Xếp hạng",
        "id": "Peringkat",
        "es": "Ranking",
        "ar": "الترتيب",
        "tl": "Ranggo",
        "fil": "Ranggo",
    },
    "offers": {
        "zh": "报价",
        "sr": "ponude",
        "pl": "oferty",
        "ja": "オファー",
        "ko": "제안",
        "th": "ข้อเสนอ",
        "vi": "báo giá",
        "id": "penawaran",
        "es": "ofertas",
        "ar": "عروض",
        "tl": "mga alok",
        "fil": "mga alok",
    },
    "Ranked by activity": {
        "zh": "按活跃度排序",
        "sr": "Rangirano po aktivnosti",
        "pl": "Według aktywności",
        "ja": "アクティビティ順",
        "ko": "활동순 정렬",
        "th": "จัดอันดับตามกิจกรรม",
        "vi": "Xếp theo hoạt động",
        "id": "Diurutkan menurut aktivitas",
        "es": "Ordenado por actividad",
        "ar": "مرتبة حسب النشاط",
        "tl": "Nakaayos ayon sa aktibidad",
        "fil": "Nakaayos ayon sa aktibidad",
    },
    "Sorted by offers": {
        "zh": "按报价数量排序",
        "sr": "Sortirano po broju ponuda",
        "pl": "Według liczby ofert",
        "ja": "オファー数順",
        "ko": "제안 수순",
        "th": "เรียงตามจำนวนข้อเสนอ",
        "vi": "Sắp xếp theo số báo giá",
        "id": "Diurutkan menurut penawaran",
        "es": "Ordenado por ofertas",
        "ar": "مرتبة حسب العروض",
        "tl": "Nakaayos ayon sa mga alok",
        "fil": "Nakaayos ayon sa mga alok",
    },
    "Newest": {
        "zh": "最新",
        "sr": "Najnovije",
        "pl": "Najnowsze",
        "ja": "最新",
        "ko": "최신",
        "th": "ใหม่ล่าสุด",
        "vi": "Mới nhất",
        "id": "Terbaru",
        "es": "Más recientes",
        "ar": "الأحدث",
        "tl": "Pinakabago",
        "fil": "Pinakabago",
    },
    "results": {
        "zh": "条结果",
        "sr": "rezultata",
        "pl": "wyników",
        "ja": "件",
        "ko": "결과",
        "th": "ผลลัพธ์",
        "vi": "kết quả",
        "id": "hasil",
        "es": "resultados",
        "ar": "نتائج",
        "tl": "mga resulta",
        "fil": "mga resulta",
    },
    "Ad Campaigns": {
        "zh": "广告活动",
        "sr": "Ad kampanje",
        "pl": "Kampanie reklamowe",
        "ja": "広告キャンペーン",
        "ko": "광고 캠페인",
        "th": "แคมเปญโฆษณา",
        "vi": "Chiến dịch quảng cáo",
        "id": "Kampanye iklan",
        "es": "Campañas publicitarias",
        "ar": "حملات إعلانية",
        "tl": "Mga kampanya sa ad",
        "fil": "Mga kampanya sa ad",
    },
    "Login Required": {
        "zh": "需要登录",
        "sr": "Potrebna prijava",
        "pl": "Wymagane logowanie",
    },
    "Market": {
        "zh": "市场",
        "sr": "Pijaca",
        "pl": "Rynek",
        "ja": "マーケット",
        "ko": "마켓",
        "th": "ตลาด",
        "vi": "Chợ",
        "id": "Pasar",
        "es": "Mercado",
        "ar": "السوق",
        "tl": "Pamilihan",
        "fil": "Pamilihan",
    },
}

PLACEHOLDER_RE = re.compile(r"(\{[^{}]+\}|</?[a-zA-Z][^>]*>)")


def flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.update(flatten(v, p))
    else:
        out[prefix] = d
    return out


def set_path(root: dict, path: str, value):
    parts = path.split(".")
    cur = root
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    cur[parts[-1]] = value


def protect(text: str):
    tokens = {}

    def repl(m):
        key = f"⟦{len(tokens)}⟧"
        tokens[key] = m.group(0)
        return key

    return PLACEHOLDER_RE.sub(repl, text), tokens


def restore(text: str, tokens: dict):
    for k, v in tokens.items():
        text = text.replace(k, v)
    return text


class TranslatorCache:
    def __init__(self):
        self.cache: dict[tuple[str, str], str] = {}
        self.clients: dict[str, GoogleTranslator] = {}

    def client(self, lang: str) -> GoogleTranslator:
        code = LANG_MAP[lang]
        if code not in self.clients:
            self.clients[code] = GoogleTranslator(source="en", target=code)
        return self.clients[code]

    def translate(self, text: str, lang: str) -> str:
        if not isinstance(text, str) or not text.strip():
            return text
        gloss = GLOSSARY.get(text, {}).get(lang)
        if gloss is not None:
            return gloss
        key = (lang, text)
        if key in self.cache:
            return self.cache[key]
        protected, tokens = protect(text)
        try:
            out = self.client(lang).translate(protected)
            time.sleep(0.05)
        except Exception as exc:  # noqa: BLE001
            print(f"  warn translate fail ({lang}): {exc!r} -> keep EN")
            out = text
        out = restore(out or text, tokens)
        self.cache[key] = out
        return out


def fill_dir(dir_path: Path, tr: TranslatorCache, create_langs: list[str] | None = None):
    en_path = dir_path / "en.json"
    if not en_path.exists():
        return
    en_obj = json.loads(en_path.read_text())
    en_flat = flatten(en_obj)

    existing = {p.stem for p in dir_path.glob("*.json")}
    langs = sorted((existing | set(create_langs or [])) - {"en"})

    for lang in langs:
        if lang not in LANG_MAP:
            print(f"  skip unknown lang {lang}")
            continue
        path = dir_path / f"{lang}.json"
        if path.exists():
            obj = json.loads(path.read_text())
        else:
            obj = {}
            print(f"  create {path.relative_to(ROOT)}")
        flat = flatten(obj)
        missing = sorted(set(en_flat) - set(flat))
        if not missing:
            print(f"  ok {path.name}")
            continue
        print(f"  fill {path.name}: {len(missing)} keys")
        for i, k in enumerate(missing, 1):
            val = en_flat[k]
            if isinstance(val, str):
                val = tr.translate(val, lang)
            set_path(obj, k, val)
            if i % 40 == 0:
                print(f"    …{i}/{len(missing)}")
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def main():
    tr = TranslatorCache()
    # procurement PC routes declare /cn /rs /pl /de /ro /ba — create those files
    pc_create = ["zh", "sr", "pl", "de", "ro", "bs", "fil"]
    for d in TARGETS:
        if not d.exists():
            print(f"missing dir {d}")
            continue
        print(f"\n## {d.relative_to(ROOT)}")
        create = pc_create if d.name == "locales" and "procurement/pc" in str(d) else None
        if create and "CebuProjects/pc-frontend" in str(d):
            create = ["zh", "sr", "pl", "fil"]
        fill_dir(d, tr, create_langs=create)
    print("\nDone.")


if __name__ == "__main__":
    main()
