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
DEFAULT_AUTHOR = "Dori Edson Dona"

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


PT_LOWERCASE_WORDS = {"de", "da", "do", "das", "dos", "e", "a", "o", "as", "os",
                       "em", "com", "para", "por", "no", "na", "nos", "nas", "um", "uma"}


def titlecase_pt(text: str) -> str:
    words = text.strip().lower().split()
    result = []
    for i, w in enumerate(words):
        if i > 0 and w in PT_LOWERCASE_WORDS:
            result.append(w)
        else:
            result.append(w[:1].upper() + w[1:])
    return " ".join(result)


FNAME_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-")
VERSE_WITH_PAREN_REF_RE = re.compile(r"^(.*)\(([^)]+)\)\s*$", re.DOTALL)


def parse_document(paragraphs: list[str], filename: str):
    if len(paragraphs) < 3:
        return None, f"{filename}: poucos parágrafos reconhecidos, pulando."

    # 1) Data: preferimos a data no início do nome do arquivo (AAAA-MM-DD-...),
    #    que é o padrão mais confiável e usado em todos os arquivos até agora.
    fname_match = FNAME_DATE_RE.match(filename)
    iso_date = f"{fname_match.group(1)}-{fname_match.group(2)}-{fname_match.group(3)}" if fname_match else None

    idx = 0
    explicit_title = None
    if DATE_RE.match(paragraphs[0]):
        # formato antigo: primeira linha do próprio documento é uma data DD/MM/AAAA
        if not iso_date:
            d = DATE_RE.match(paragraphs[0])
            dd, mm, yyyy = d.groups()
            iso_date = f"{yyyy}-{mm}-{dd}"
        idx = 1
    else:
        explicit_title = paragraphs[0].strip()
        idx = 1

    if not iso_date:
        return None, (
            f"{filename}: não encontrei uma data válida — nem no início do nome "
            f"do arquivo (AAAA-MM-DD-...), nem como primeira linha do texto. Pulando."
        )

    if idx >= len(paragraphs):
        return None, f"{filename}: documento incompleto após o título/data. Pulando."

    # 2) Versículo + referência: podem vir de duas formas —
    #    a) uma linha só, terminando com "(Referência)" entre parênteses
    #    b) duas linhas separadas: referência, depois o texto do versículo
    candidate = paragraphs[idx]
    paren_match = VERSE_WITH_PAREN_REF_RE.match(candidate)
    if paren_match:
        verse_text = paren_match.group(1).strip().translate(SUPERSCRIPT_DIGITS).strip()
        verse_text = re.sub(r"\s*;\s*", "; ", verse_text)
        verse_ref = paren_match.group(2).strip()
        idx += 1
    else:
        if idx + 1 >= len(paragraphs):
            return None, f"{filename}: não consegui identificar o versículo e a referência. Pulando."
        verse_ref = candidate
        verse_text = paragraphs[idx + 1].translate(SUPERSCRIPT_DIGITS).strip()
        verse_text = re.sub(r"\s*;\s*", "; ", verse_text)
        idx += 2

    rest = paragraphs[idx:]
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
                candidate2 = rest[i + 1]
                if len(candidate2) <= 60 and not candidate2.endswith((".", "!", "?")):
                    author = candidate2
            break
        reflection.append(p)
        i += 1

    if not reflection:
        return None, f"{filename}: não encontrei parágrafos de reflexão. Pulando."

    if explicit_title:
        title = titlecase_pt(explicit_title)
        needs_review = False
    else:
        title = f"Meditação em {verse_ref}"
        needs_review = True
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
        "needsTitleReview": needs_review,
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
        rotulo = "título provisório" if e.get("needsTitleReview") else "título"
        print(f"  • {e['date']}  {e['verseRef']:<20}  {rotulo}: \"{e['title']}\"")
        print(f"    áudio esperado: {e['audio']}")

    if any(e.get("needsTitleReview") for e in added):
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
