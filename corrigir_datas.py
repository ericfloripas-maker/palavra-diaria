# corrigir_datas.py
# Corrige as datas dos devocionais importados em lote, que ficaram com
# datas antigas (herdadas do nome do arquivo original) em vez de datas
# futuras/sequenciais para o site novo.
#
# Mantem intactos os 12 devocionais originais (11 a 28 de agosto de 2026),
# que ja estavam com data correta. Todos os outros sao reordenados pela
# data antiga (para preservar a ordem/sequencia pretendida) e recebem
# novas datas sequenciais, pulando fins de semana, comecando logo apos
# 28-08-2026.
#
# Alem de corrigir o campo "date" no JSON, este script tambem:
#   - Renomeia o arquivo .odt correspondente em textos/ para usar a nova data
#   - Atualiza o campo "source" no JSON para apontar pro novo nome de arquivo
#
# NAO mexe nos arquivos de audio nem no campo "audio" - por decisao
# consciente, esses permanecem com o nome antigo.
#
# Uso: py corrigir_datas.py

import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
CATALOG_PATH = PROJECT_DIR / "devocionais.json"
BACKUP_PATH = PROJECT_DIR / "devocionais.json.bak"
TEXTOS_DIR = PROJECT_DIR / "textos"

DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

# As 12 datas originais que ja estavam corretas - NAO mexer nelas
DATAS_CORRETAS_ORIGINAIS = {
    "2026-08-11", "2026-08-15", "2026-08-17", "2026-08-18",
    "2026-08-19", "2026-08-20", "2026-08-21", "2026-08-24",
    "2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28",
}

ULTIMA_DATA_CORRETA = datetime.strptime("2026-08-28", "%Y-%m-%d")


def proximo_dia_util(data):
    prox = data + timedelta(days=1)
    while prox.weekday() >= 5:  # 5=sabado, 6=domingo
        prox += timedelta(days=1)
    return prox


def novo_nome_arquivo(nome_antigo, nova_data):
    """Troca so o prefixo de data (10 primeiros chars) do nome do arquivo."""
    if DATE_PREFIX_RE.match(nome_antigo):
        return nova_data + nome_antigo[10:]
    # se por algum motivo nao comecar com data, so prefixa
    return f"{nova_data}-{nome_antigo}"


def main():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data if isinstance(data, list) else data.get("devocionais", data)

    mantidos = [item for item in items if item.get("date") in DATAS_CORRETAS_ORIGINAIS]
    para_corrigir = [item for item in items if item.get("date") not in DATAS_CORRETAS_ORIGINAIS]

    # ordena pela data antiga (mesmo errada) para preservar a sequencia pretendida
    para_corrigir.sort(key=lambda item: item.get("date", ""))

    print(f"Devocionais mantidos (data original correta): {len(mantidos)}")
    print(f"Devocionais a corrigir (data e arquivo .odt serao renomeados): {len(para_corrigir)}")
    print()

    # backup do JSON antes de qualquer alteracao
    shutil.copy(CATALOG_PATH, BACKUP_PATH)
    print(f"Backup do JSON salvo em: {BACKUP_PATH}")
    print()

    atual = ULTIMA_DATA_CORRETA
    previa = []
    arquivos_nao_encontrados = []

    for item in para_corrigir:
        atual = proximo_dia_util(atual)
        nova_data = atual.strftime("%Y-%m-%d")
        data_antiga = item.get("date")
        titulo = item.get("title", "")

        source_antigo = item.get("source")
        source_novo = None

        if source_antigo:
            source_novo = novo_nome_arquivo(source_antigo, nova_data)
            caminho_antigo = TEXTOS_DIR / source_antigo
            caminho_novo = TEXTOS_DIR / source_novo

            if caminho_antigo.exists():
                caminho_antigo.rename(caminho_novo)
            else:
                arquivos_nao_encontrados.append((source_antigo, titulo))
                # mesmo sem o arquivo fisico, atualizamos o JSON para o nome esperado

        item["date"] = nova_data
        if source_novo:
            item["source"] = source_novo

        previa.append((data_antiga, nova_data, source_antigo, source_novo, titulo))

    print("=== Previa (5 primeiras e 5 ultimas) ===")
    for antiga, nova, src_antigo, src_novo, titulo in previa[:5]:
        print(f"  {antiga} -> {nova}   | {titulo}")
        print(f"      {src_antigo}  ->  {src_novo}")
    print("  ...")
    for antiga, nova, src_antigo, src_novo, titulo in previa[-5:]:
        print(f"  {antiga} -> {nova}   | {titulo}")
        print(f"      {src_antigo}  ->  {src_novo}")

    print()
    print(f"Primeira nova data: {previa[0][1]}")
    print(f"Ultima nova data:   {previa[-1][1]}")

    if arquivos_nao_encontrados:
        print()
        print(f"AVISO: {len(arquivos_nao_encontrados)} arquivo(s) .odt esperado(s) nao foram encontrados em textos/ (o JSON foi atualizado mesmo assim, mas confira depois):")
        for nome, titulo in arquivos_nao_encontrados:
            print(f"  - {nome}  ({titulo})")

    # salva JSON atualizado, mantendo a mesma estrutura (lista ou dict)
    if isinstance(data, list):
        data_out = mantidos + para_corrigir
        data_out.sort(key=lambda item: item.get("date", ""))
    else:
        combinado = mantidos + para_corrigir
        combinado.sort(key=lambda item: item.get("date", ""))
        data["devocionais"] = combinado
        data_out = data

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2)

    print()
    print("Concluido! devocionais.json atualizado e arquivos .odt renomeados.")
    print("Se algo der errado, o backup do JSON esta em devocionais.json.bak")
    print("(os arquivos .odt renomeados nao tem backup automatico - se precisar desfazer,")
    print(" avise que eu te ajudo a reverter usando o mapeamento impresso acima).")


if __name__ == "__main__":
    main()
