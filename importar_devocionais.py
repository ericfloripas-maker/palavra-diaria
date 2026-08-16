#!/usr/bin/env python3
"""
Importador de devocionais para a Palavra Diária.

O que faz:
- Lê todo arquivo .odt (ou .docx) dentro da pasta textos/
- Reconhece automaticamente: data, referência bíblica, versículo, parágrafos
  de reflexão e oração, no mesmo formato que os documentos já usados
- Adiciona cada um como uma nova entrada em devocionais.json
- Não duplica: se rodar de novo com os mesmos arquivos, eles são ignorados
- Nunca apaga nada que já está no catálogo

Como usar:
    1. Coloque os arquivos .odt (ou .docx) dentro da pasta textos/
    2. No terminal do VS Code, rode:  python importar_devocionais.py
    3. Leia o resumo no final — ele avisa quais devocionais precisam de
       revisão de título antes de publicar

Formato esperado de cada documento (um parágrafo por linha, nesta ordem):
    DD/MM/AAAA
    Referência bíblica (ex: Salmos 90:5,6)
    Texto do versículo
    (um ou mais parágrafos de reflexão)
    Oração: texto da oração
    (opcional) Nome do autor, sozinho na última linha
"""

import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.sax.saxutils import unescape

PROJECT_DIR = Path(__file__).parent
TEXTOS_DIR = PROJECT_DIR / "textos"
CATALOG_PATH = PROJECT_DIR / "devocionais.json"
DEFAULT_AUTHOR = "Doriedson Doná"

DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
SUPERSCRIPT_DIGITS = str.maketrans("", "", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def strip_tags(xml_text: str) -> list[str]:
    """Converte o XML do documento numa lista de parágrafos de texto puro."""
    xml_text = re.sub(r"<text:p[^>]*>", "\n§PARA§", xml_text)
    xml_text = re.sub(r"<w:p[^>]*>", "\n§PARA§", xml_text)  # docx
    xml_text = re.sub(r"<[^>]+>", "", xml_text)
    text = unescape(xml_text)
    raw_paragraphs = text.split("§PARA§")
    paragraphs = [p.strip() for p in raw_paragraphs]
    return [p for p in paragraphs if p]


def read_odt(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        xml_text = z.read("content.xml").decode("utf-8")
    return strip_tags(xml_text)


def read_docx(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        xml_text = z.read("word/document.xml").decode("utf-8")
    return strip_tags(xml_text)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text or "devocional"


def parse_document(paragraphs: list[str], filename: str):
    if len(paragraphs) < 3:
        return None, f"{filename}: poucos parágrafos reconhecidos, pulando."

    date_match = DATE_RE.match(paragraphs[0])
    if not date_match:
        return None, (
            f"{filename}: não encontrei uma data no formato DD/MM/AAAA "
            f"na primeira linha (achei: \"{paragraphs[0][:40]}\"). Pulando."
        )
    dd, mm, yyyy = date_match.groups()
    iso_date = f"{yyyy}-{mm}-{dd}"

    verse_ref = paragraphs[1]
    verse_text = paragraphs[2].translate(SUPERSCRIPT_DIGITS).strip()
    verse_text = re.sub(r"\s*;\s*", "; ", verse_text)

    rest = paragraphs[3:]
    reflection = []
    prayer = None
    author = None

    i = 0
    while i < len(rest):
        p = rest[i]
        if p.lower().startswith("oração"):
            prayer = re.sub(r"^ora[çc][ãa]o:?\s*", "", p, flags=re.IGNORECASE).strip()
            # linha seguinte, se curta e sem terminar em pontuação forte, é o autor
            if i + 1 < len(rest):
                candidate = rest[i + 1]
                if len(candidate) <= 60 and not candidate.endswith((".", "!", "?")):
                    author = candidate
            break
        reflection.append(p)
        i += 1

    if not reflection:
        return None, f"{filename}: não encontrei parágrafos de reflexão. Pulando."

    title = f"Meditação em {verse_ref}"
    slug = slugify(title)

    entry = {
        "date": iso_date,
        "slug": slug,
        "title": title,
        "verseRef": verse_ref,
        "verseText": verse_text,
        "reflection": reflection,
        "author": author or DEFAULT_AUTHOR,
        "audio": f"audio/{iso_date}-{slug}.mp3",
        "tags": [],
        "relatedThemes": [],
        "source": filename,
        "needsTitleReview": True,
    }
    if prayer:
        entry["prayer"] = prayer

    return entry, None


def main():
    if not TEXTOS_DIR.exists():
        print(f"Pasta não encontrada: {TEXTOS_DIR}")
        sys.exit(1)

    if CATALOG_PATH.exists():
        with open(CATALOG_PATH, encoding="utf-8") as f:
            catalog = json.load(f)
    else:
        catalog = []

    already_imported = {e.get("source") for e in catalog if e.get("source")}
    existing_slugs = {e["slug"] for e in catalog}

    files = sorted(
        [p for p in TEXTOS_DIR.iterdir() if p.suffix.lower() in (".odt", ".docx")]
    )

    if not files:
        print(f"Nenhum arquivo .odt ou .docx encontrado em {TEXTOS_DIR}")
        return

    added = []
    skipped = []
    errors = []

    for path in files:
        if path.name in already_imported:
            skipped.append(path.name)
            continue

        try:
            paragraphs = read_odt(path) if path.suffix.lower() == ".odt" else read_docx(path)
        except Exception as exc:
            errors.append(f"{path.name}: erro ao abrir o arquivo ({exc})")
            continue

        entry, error = parse_document(paragraphs, path.name)
        if error:
            errors.append(error)
            continue

        # evita colisão de slug (dois devocionais com título default igual)
        base_slug = entry["slug"]
        counter = 2
        while entry["slug"] in existing_slugs:
            entry["slug"] = f"{base_slug}-{counter}"
            entry["audio"] = f"audio/{entry['date']}-{entry['slug']}.mp3"
            counter += 1
        existing_slugs.add(entry["slug"])

        catalog.append(entry)
        added.append(entry)

    if added:
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\n{len(added)} devocional(is) adicionado(s):")
    for e in added:
        print(f"  • {e['date']}  {e['verseRef']:<20}  título provisório: \"{e['title']}\"")
        print(f"    áudio esperado: {e['audio']}")

    if added:
        print(
            "\n⚠ Revise o título de cada um acima no devocionais.json antes de publicar "
            "(procure needsTitleReview: true) — o script só consegue gerar um título "
            "provisório, não um título editorial de verdade."
        )

    if skipped:
        print(f"\n{len(skipped)} arquivo(s) já haviam sido importados antes, ignorado(s):")
        for name in skipped:
            print(f"  • {name}")

    if errors:
        print(f"\n{len(errors)} arquivo(s) com problema:")
        for msg in errors:
            print(f"  • {msg}")


if __name__ == "__main__":
    main()
