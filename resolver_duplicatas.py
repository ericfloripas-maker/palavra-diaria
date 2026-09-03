# resolver_duplicatas.py
# Resolve as duplicatas de data encontradas em 2026-08-11 e 2026-08-15:
#   - Apaga as 2 entradas redundantes (mesmo conteudo do original, reimportado
#     por engano) - remove do JSON e tambem os arquivos .mp3 e .odt correspondentes
#   - Move a entrada genuinamente diferente ("A Fragilidade da Vida Humana",
#     11/08) para a proxima data disponivel na sequencia (dia util seguinte
#     a ultima data ja usada no catalogo), sem mexer no nome do arquivo de audio,
#     mas renomeando o .odt correspondente
#
# Uso: py resolver_duplicatas.py

import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
CATALOG_PATH = PROJECT_DIR / "devocionais.json"
TEXTOS_DIR = PROJECT_DIR / "textos"
AUDIO_DIR = PROJECT_DIR / "audio"

DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")

# Entradas redundantes a apagar (identificadas por titulo + source exatos)
PARA_APAGAR = [
    {"title": "Meditação em Salmos 90:5,6", "source": "2026-08-11-como-um-sono-como-a-relva.odt"},
    {"title": "Recém-chegados, Mas de Partida", "source": "2026-08-15-recem-chegados-mas-de-partida.odt"},
]

# Entrada a mover (identificada por titulo + source exatos)
PARA_MOVER = {"title": "A Fragilidade da Vida Humana", "source": "2026-08-11-Sl_90_3e4-a-fragilidade-da-vida-humana.odt"}


def proximo_dia_util(data):
    prox = data + timedelta(days=1)
    while prox.weekday() >= 5:
        prox += timedelta(days=1)
    return prox


def novo_nome_arquivo(nome_antigo, nova_data):
    if DATE_PREFIX_RE.match(nome_antigo):
        return nova_data + nome_antigo[10:]
    return f"{nova_data}-{nome_antigo}"


def apagar_arquivo_se_existir(caminho, descricao):
    if caminho.exists():
        caminho.unlink()
        print(f"  Apagado: {caminho.relative_to(PROJECT_DIR)}")
    else:
        print(f"  ({descricao} nao encontrado em disco, so removendo do JSON: {caminho.name})")


def main():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data if isinstance(data, list) else data.get("devocionais", data)

    # backup versionado (nao sobrescreve o backup anterior)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = PROJECT_DIR / f"devocionais.json.bak-{ts}"
    shutil.copy(CATALOG_PATH, backup_path)
    print(f"Backup salvo em: {backup_path.name}")
    print()

    # --- Apagar redundantes ---
    print("=== Apagando entradas redundantes ===")
    restantes = []
    apagados = 0
    for item in items:
        match = any(
            item.get("title") == alvo["title"] and item.get("source") == alvo["source"]
            for alvo in PARA_APAGAR
        )
        if match:
            print(f"Apagando: {item.get('title')} ({item.get('date')})")
            audio_path = PROJECT_DIR / item.get("audio", "")
            apagar_arquivo_se_existir(audio_path, "audio")
            if item.get("source"):
                apagar_arquivo_se_existir(TEXTOS_DIR / item["source"], "texto")
            apagados += 1
        else:
            restantes.append(item)

    print(f"Total apagado: {apagados} entrada(s)")
    print()

    # --- Mover a diferente ---
    print("=== Movendo entrada genuinamente diferente ===")
    ultima_data = max(datetime.strptime(item["date"], "%Y-%m-%d") for item in restantes if item.get("date"))
    nova_data = proximo_dia_util(ultima_data).strftime("%Y-%m-%d")

    movido = False
    for item in restantes:
        if item.get("title") == PARA_MOVER["title"] and item.get("source") == PARA_MOVER["source"]:
            data_antiga = item["date"]
            source_antigo = item["source"]
            source_novo = novo_nome_arquivo(source_antigo, nova_data)

            caminho_antigo = TEXTOS_DIR / source_antigo
            caminho_novo = TEXTOS_DIR / source_novo
            if caminho_antigo.exists():
                caminho_antigo.rename(caminho_novo)
                print(f"  Renomeado .odt: {source_antigo} -> {source_novo}")
            else:
                print(f"  AVISO: {source_antigo} nao encontrado em textos/, so atualizando o JSON")

            item["date"] = nova_data
            item["source"] = source_novo
            print(f"  '{item.get('title')}': {data_antiga} -> {nova_data}")
            movido = True
            break

    if not movido:
        print("  AVISO: entrada a mover nao foi encontrada - nada foi alterado nessa etapa.")

    # salva
    if isinstance(data, list):
        data_out = restantes
        data_out.sort(key=lambda item: item.get("date", ""))
    else:
        restantes.sort(key=lambda item: item.get("date", ""))
        data["devocionais"] = restantes
        data_out = data

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2)

    print()
    print("Concluido! devocionais.json atualizado.")


if __name__ == "__main__":
    main()
