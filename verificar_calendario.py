# verificar_calendario.py
# Verifica o devocionais.json em busca de:
#  1) Datas duplicadas (dois devocionais na mesma data)
#  2) Lacunas no calendario (dias uteis - seg a sex - sem devocional)
#
# Uso: py verificar_calendario.py

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

CATALOG_PATH = Path(__file__).parent / "devocionais.json"

def main():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # aceita tanto uma lista quanto um dict com chave "devocionais"
    items = data if isinstance(data, list) else data.get("devocionais", data)

    datas_str = [item["date"] for item in items if "date" in item]
    datas = sorted(datetime.strptime(d, "%Y-%m-%d") for d in datas_str)

    print(f"Total de devocionais no catalogo: {len(datas)}")
    print(f"Periodo: {datas[0].strftime('%Y-%m-%d')} a {datas[-1].strftime('%Y-%m-%d')}")
    print()

    # 1) Duplicatas
    contagem = Counter(datas_str)
    duplicadas = {d: c for d, c in contagem.items() if c > 1}
    print("=== DATAS DUPLICADAS ===")
    if duplicadas:
        for d, c in sorted(duplicadas.items()):
            print(f"  {d} aparece {c} vezes")
    else:
        print("  Nenhuma duplicata encontrada.")
    print()

    # 2) Lacunas em dias uteis (segunda a sexta)
    print("=== LACUNAS EM DIAS UTEIS (seg-sex) ===")
    datas_set = set(datas_str)
    atual = datas[0]
    fim = datas[-1]
    lacunas = []
    while atual <= fim:
        if atual.weekday() < 5:  # 0=segunda ... 4=sexta
            chave = atual.strftime("%Y-%m-%d")
            if chave not in datas_set:
                lacunas.append(chave)
        atual += timedelta(days=1)

    if lacunas:
        for d in lacunas:
            dia_semana = datetime.strptime(d, "%Y-%m-%d").strftime("%A")
            print(f"  {d} ({dia_semana}) - sem devocional")
        print(f"\n  Total de lacunas: {len(lacunas)}")
    else:
        print("  Nenhuma lacuna encontrada - todos os dias uteis do periodo tem devocional.")

if __name__ == "__main__":
    main()
