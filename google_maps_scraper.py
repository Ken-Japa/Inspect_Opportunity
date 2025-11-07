# Autor: Ken
# Objetivo: Buscar dados de empresas locais no Google Maps e gerar CSV para análise

import os
import time
import random
import csv
import json
import logging

import pandas as pd
import serpapi
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
    """Busca empresas no Google Maps via SerpAPI com retentativas e backoff exponencial."""
    logging.info(f"🔍 Buscando: {nicho} em {cidade}...")
    params = {
        "engine": "google_maps",
        "q": f"{nicho} {cidade}",
        "type": "search",
        "hl": "pt",
        "api_key": API_KEY
    }

    max_retries = 5
    initial_delay = 1  # segundos

    for attempt in range(max_retries):
        try:
            client = serpapi.Client(api_key=API_KEY)
            results = client.search(params)

            if "error" in results:
                error_message = results["error"]
                if "daily limit" in error_message.lower() or "api key" in error_message.lower():
                    logging.error(f"❌ Erro fatal da SerpAPI para {nicho} em {cidade}: {error_message}. Não será feita nova tentativa.")
                    return []
                else:
                    logging.warning(f"⚠️ Erro da SerpAPI para {nicho} em {cidade} (tentativa {attempt + 1}/{max_retries}): {error_message}")
            else:
                return results.get("local_results", [])

        except Exception as e:
            logging.warning(f"⚠️ Erro ao chamar a SerpAPI para {nicho} em {cidade} (tentativa {attempt + 1}/{max_retries}): {e}")

        if attempt < max_retries - 1:
            delay = initial_delay * (2 ** attempt) + random.uniform(0, 1) # Backoff exponencial com jitter
            logging.info(f"Aguardando {delay:.2f} segundos antes de tentar novamente...")
            time.sleep(delay)

    logging.error(f"❌ Falha ao buscar empresas para {nicho} em {cidade} após {max_retries} tentativas.")
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

    if not cidades:
        logging.error("❌ A lista de cidades está vazia. Verifique o arquivo cidades.csv ou cidades.json.")
        return

    if not nichos:
        logging.error("❌ A lista de nichos está vazia. Verifique o arquivo nichos.csv ou nichos.json.")
        return

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
