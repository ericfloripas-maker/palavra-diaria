#!/usr/bin/env python3
"""
Importador de devocionais para a Palavra Diária.

O que faz:
- Lê todo arquivo .odt (ou .docx) dentro da pasta textos/
- Reconhece automaticamente: data (do nome do arquivo), título, versículo,
  referência bíblica, parágrafos de reflexão e oração
- Sugere automaticamente 1-2 temas (tags) com base em palavras-chave do
  texto — não é uma análise profunda, é um dicionário de temas comuns,
  mas cobre a maioria dos casos sem precisar preencher na mão
- Adiciona cada um como uma nova entrada em devocionais.json
- Não duplica: se rodar de novo com os mesmos arquivos, eles são ignorados
- Nunca apaga nada que já está no catálogo

Como usar:
    1. Coloque os arquivos .odt (ou .docx) dentro da pasta textos/
    2. No terminal do VS Code, rode:  py importar_devocionais.py
    3. Leia o resumo no final — ele avisa quais devocionais precisam de
       revisão de título ou tema antes de publicar

Para preencher os temas de devocionais JÁ importados antes (que ficaram
com "tags": [] vazio), rode:
    py importar_devocionais.py --preencher-tags-existentes
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
FNAME_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-")
VERSE_WITH_PAREN_REF_RE = re.compile(r"^(.*)\(([^)]+)\)\s*$", re.DOTALL)
SUPERSCRIPT_DIGITS = str.maketrans("", "", "⁰¹²³⁴⁵⁶⁷⁸⁹")

PT_LOWERCASE_WORDS = {"de", "da", "do", "das", "dos", "e", "a", "o", "as", "os",
                       "em", "com", "para", "por", "no", "na", "nos", "nas", "um", "uma"}

# --- dicionário de temas: tema -> palavras-chave que indicam esse tema ---
# (tudo em minúsculo e sem acento; o texto é normalizado antes de comparar)
TEMAS_PALAVRAS_CHAVE = {
    "Eternidade": ["eternidade", "eterno", "eterna", "para sempre", "permanece", "perpetuo"],
    "Soberania": ["soberano", "soberania", "autoridade", "dominio", "reina", "todo-poderoso", "onipotente"],
    "Confianca": ["confia", "confianca", "confie", "confiar"],
    "Fe": ["fe ", " fe.", "crer", "creio", "cre em", "acreditar"],
    "Ansiedade": ["ansiedade", "ansioso", "ansiosa", "angustia", "afligido", "aflicao"],
    "Perseveranca": ["persevera", "perseveranca", "resistir", "suportar", "firmeza"],
    "Graca": ["graca", "misericordia", "perdao", "perdoa"],
    "Oracao": ["oracao", "orar", "clama", "clamor", "suplica"],
    "Obediencia": ["obedece", "obediencia", "submissao", "submeter"],
    "Coragem": ["coragem", "corajoso", "temor", "nao temas", "destemido"],
    "Sabedoria": ["sabedoria", "sabio", "entendimento", "discernimento"],
    "Adoracao": ["adoracao", "adora", "louvor", "louva", "gloria a deus"],
    "Justica": ["justica", "justo", "juizo", "julgamento"],
    "Amor": ["amor", "amoroso", "ama a", "amai"],
    "Esperanca": ["esperanca", "espera em", "aguarda"],
    "Mortalidade": ["morte", "mortal", "po da terra", "efemero", "passageiro", "transitorio"],
    "Provisao": ["provisao", "prove", "sustento", "sustenta"],
    "Santidade": ["santidade", "santo", "consagracao", "puro", "pureza"],
    "Humildade": ["humildade", "humilde", "humilhar", "soberba", "orgulho"],
    "Gratidao": ["gratidao", "grato", "agradece", "acoes de gracas"],
}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def sugerir_tags(entry: dict, max_tags: int = 2) -> list:
    """Sugere temas com base na contagem de palavras-chave no texto do devocional."""
    texto_completo = normalizar(
        entry.get("title", "") + " " +
        entry.get("verseText", "") + " " +
        " ".join(entry.get("reflection", []))
    )
    pontuacao = {}
    for tema, palavras in TEMAS_PALAVRAS_CHAVE.items():
        contagem = sum(texto_completo.count(normalizar(p)) for p in palavras)
        if contagem > 0:
            pontuacao[tema] = contagem

    temas_ordenados = sorted(pontuacao.items(), key=lambda x: -x[1])
    return [tema for tema, _ in temas_ordenados[:max_tags]]


def titlecase_pt(text: str) -> str:
    words = text.strip().lower().split()
    result = []
    for i, w in enumerate(words):
        if i > 0 and w in PT_LOWERCASE_WORDS:
            result.append(w)
        else:
            result.append(w[:1].upper() + w[1:])
    return " ".join(result)


def strip_tags(xml_text: str) -> list:
    xml_text = re.sub(r"<text:p[^>]*>", "\n§PARA§", xml_text)
    xml_text = re.sub(r"<w:p[^>]*>", "\n§PARA§", xml_text)
    xml_text = re.sub(r"<[^>]+>", "", xml_text)
    text = unescape(xml_text)
    raw_paragraphs = text.split("§PARA§")
    paragraphs = [p.strip() for p in raw_paragraphs]
    return [p for p in paragraphs if p]


def read_odt(path: Path) -> list:
    with zipfile.ZipFile(path) as z:
        xml_text = z.read("content.xml").decode("utf-8")
    return strip_tags(xml_text)


def read_docx(path: Path) -> list:
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


def parse_document(paragraphs: list, filename: str):
    if len(paragraphs) < 3:
        return None, f"{filename}: poucos parágrafos reconhecidos, pulando."

    fname_match = FNAME_DATE_RE.match(filename)
    iso_date = f"{fname_match.group(1)}-{fname_match.group(2)}-{fname_match.group(3)}" if fname_match else None

    idx = 0
    explicit_title = None
    if DATE_RE.match(paragraphs[0]):
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

    tags_sugeridas = sugerir_tags(entry, max_tags=2)
    entry["tags"] = tags_sugeridas
    entry["relatedThemes"] = sugerir_tags(entry, max_tags=5)
    entry["needsTagReview"] = len(tags_sugeridas) == 0

    return entry, None


def preencher_tags_existentes():
    """Preenche tags automaticamente em entradas já existentes que estão com tags vazio."""
    if not CATALOG_PATH.exists():
        print("devocionais.json não encontrado.")
        return

    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    atualizados = []
    for entry in catalog:
        if not entry.get("tags"):
            sugeridas = sugerir_tags(entry, max_tags=2)
            if sugeridas:
                entry["tags"] = sugeridas
                entry["relatedThemes"] = sugerir_tags(entry, max_tags=5)
                entry["needsTagReview"] = False
                atualizados.append((entry["date"], entry["title"], sugeridas))
            else:
                entry["needsTagReview"] = True

    if atualizados:
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\n{len(atualizados)} devocional(is) atualizado(s) com tags novas:")
    for date, title, tags in atualizados:
        print(f"  • {date}  {title}  → {', '.join('#' + t for t in tags)}")

    sem_tag = [e for e in catalog if not e.get("tags")]
    if sem_tag:
        print(f"\n{len(sem_tag)} devocional(is) ainda sem tema identificado automaticamente:")
        for e in sem_tag:
            print(f"  • {e['date']}  {e['title']}  (marcar tema manualmente no JSON)")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--preencher-tags-existentes":
        preencher_tags_existentes()
        return

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
        if e["tags"]:
            print(f"    temas sugeridos: {', '.join('#' + t for t in e['tags'])}")
        else:
            print(f"    ⚠ nenhum tema reconhecido automaticamente — preencher \"tags\" manualmente")
        print(f"    áudio esperado: {e['audio']}")

    if any(e.get("needsTitleReview") for e in added):
        print(
            "\n⚠ Revise o título de cada um acima no devocionais.json antes de publicar "
            "(procure needsTitleReview: true)."
        )

    if any(e.get("needsTagReview") for e in added):
        print(
            "⚠ Alguns devocionais ficaram sem tema reconhecido automaticamente "
            "(procure needsTagReview: true) — preencha \"tags\" manualmente nesses casos."
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