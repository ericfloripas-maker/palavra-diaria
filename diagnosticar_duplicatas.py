# diagnosticar_duplicatas.py
# Mostra os detalhes completos de cada devocional cuja data esta duplicada,
# para ajudar a decidir qual e o original (que deve manter a data) e quais
# sao do arquivo historico (que precisam ser movidos para outra data).
#
# Uso: py diagnosticar_duplicatas.py

import json
from collections import Counter
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "devocionais.json"


def main():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data if isinstance(data, list) else data.get("devocionais", data)

    datas = [item.get("date") for item in items]
    contagem = Counter(datas)
    duplicadas = sorted(d for d, c in contagem.items() if c > 1)

    if not duplicadas:
        print("Nenhuma data duplicada encontrada.")
        return

    for data_dup in duplicadas:
        print(f"=== Data duplicada: {data_dup} ===")
        entradas = [item for item in items if item.get("date") == data_dup]
        for i, item in enumerate(entradas, 1):
            print(f"  --- Entrada {i} ---")
            print(f"    Titulo: {item.get('title')}")
            print(f"    Source: {item.get('source')}")
            print(f"    VerseRef: {item.get('verseRef')}")
            print(f"    Audio: {item.get('audio')}")
            print(f"    needsTitleReview: {item.get('needsTitleReview')}")
        print()


if __name__ == "__main__":
    main()
