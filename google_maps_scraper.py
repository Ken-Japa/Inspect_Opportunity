# Autor: Ken
# Objetivo: Buscar dados de empresas locais no Google Maps e gerar CSV para análise

import os
import time
import random
import csv
import json
import logging

import pandas as pd
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Configuração do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def carregar_lista_de_arquivo(nome_arquivo, tipo):
    """Carrega uma lista de um arquivo CSV ou JSON."""
    caminho_csv = f"{nome_arquivo}.csv"
    caminho_json = f"{nome_arquivo}.json"

    if os.path.exists(caminho_csv):
        logging.info(f"Carregando {tipo} de {caminho_csv}")
        df = pd.read_csv(caminho_csv, header=None)
        return df[0].tolist()
    elif os.path.exists(caminho_json):
        logging.info(f"Carregando {tipo} de {caminho_json}")
        with open(caminho_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        logging.warning(f"Nenhum arquivo encontrado para {tipo} em {caminho_csv} ou {caminho_json}. Usando lista padrão.")
        return None

# ----------------------------------------
# CONFIGURAÇÕES
# ----------------------------------------
# Configurações
load_dotenv() # Carrega as variáveis de ambiente do arquivo .env
API_KEY = os.getenv("SERPAPI_API_KEY")
if not API_KEY:
    raise ValueError("A variável de ambiente SERPAPI_API_KEY não está definida.")

# ----------------------------------------
# FUNÇÃO PRINCIPAL
# ----------------------------------------
def buscar_empresas(nicho, cidade):
    """Busca empresas no Google Maps via SerpAPI"""
    logging.info(f"🔍 Buscando: {nicho} em {cidade}...")
    params = {
        "engine": "google_maps",
        "q": f"{nicho} {cidade}",
        "type": "search",
        "hl": "pt",
        "api_key": API_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            logging.warning(f"⚠️ Erro da SerpAPI para {nicho} em {cidade}: {results["error"]}")
            return []

    except Exception as e:
        logging.error(f"⚠️ Erro ao chamar a SerpAPI para {nicho} em {cidade}: {e}")
        return []

    empresas = []
    for local in results.get("local_results", []):
        empresas.append({
            "nicho": nicho,
            "cidade": cidade,
            "nome": local.get("title"),
            "nota": local.get("rating"),
            "reviews": local.get("reviews"),
            "endereco": local.get("address"),
            "telefone": local.get("phone"),
            "site": local.get("website"),
            "categoria": local.get("type"),
        })

    return empresas


# ----------------------------------------
# EXECUÇÃO PRINCIPAL
# ----------------------------------------
def main():

    cidades = carregar_lista_de_arquivo("cidades", "cidades")
    nichos = carregar_lista_de_arquivo("nichos", "nichos")

    todas_empresas = []

    for cidade in cidades:
        for nicho in nichos:
            try:
                dados = buscar_empresas(nicho, cidade)
                todas_empresas.extend(dados)
                # Atraso com jitter para evitar rate limiting
                sleep_time = random.uniform(2, 5)  # Atraso entre 2 e 5 segundos
                logging.info(f"Aguardando {sleep_time:.2f} segundos antes da próxima requisição...")
                time.sleep(sleep_time)
            except Exception as e:
                logging.error(f"⚠️ Erro em {nicho} - {cidade}: {e}")

    # Converter para DataFrame
    df = pd.DataFrame(todas_empresas)

    # Converter colunas numéricas
    for col in ["nota", "reviews"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Salvar CSV
    df.to_csv("dados_empresas_googlemaps.csv", index=False, encoding="utf-8-sig")
    logging.info(f"\n✅ Dados salvos em 'dados_empresas_googlemaps.csv' com {len(df)} registros.")

    # Exemplo de resumo simples
    resumo = df.groupby(["cidade", "nicho"]).agg({
        "nome": "count",
        "nota": "mean",
        "reviews": "sum"
    }).rename(columns={
        "nome": "quantidade_empresas",
        "nota": "nota_media",
        "reviews": "total_reviews"
    })

    logging.info("\n📊 Resumo inicial:")
    logging.info(resumo)

if __name__ == "__main__":
    main()
