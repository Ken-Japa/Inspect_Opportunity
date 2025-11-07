# Objetivo: Buscar dados de empresas locais no Google Maps e gerar CSV para análise

import os
import time
import random
import json
import logging
import datetime

import pandas as pd
import serpapi
from serpapi import GoogleSearch
from dotenv import load_dotenv

# Configuração do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def carregar_lista_de_arquivo(nome_arquivo, tipo):
    """Carrega uma lista de um arquivo CSV ou JSON."""
    caminho_csv = f"input/{nome_arquivo}.csv"
    caminho_json = f"input/{nome_arquivo}.json"

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
    """Busca empresas no Google Maps via SerpAPI com retentativas e backoff exponencial. Fallback para engine 'google_maps_search'."""
    logging.info(f"🔍 Buscando: {nicho} em {cidade}...")
    engines = ["google_local", "google_maps"]
    max_retries = 2
    initial_delay = 1
    
    for engine in engines:
        logging.info(f"🧭 Usando engine: {engine}")
        params = {
            "engine": engine,
            "q": f"{nicho} em {cidade}, Minas Gerais",
            "hl": "pt",
            "gl": "br",
            "api_key": API_KEY,
        }

        for attempt in range(max_retries):
            try:
                search = GoogleSearch(params)
                results = search.get_dict()

                # detecta erro explícito
                if "error" in results:
                    logging.warning(
                        f"⚠️ Erro da SerpAPI ({engine}) para {nicho}: {results['error']} (tentativa {attempt+1}/{max_retries})"
                    )
                else:
                    # tenta extrair dados no formato 1 ou 2
                    local_results = []
                    if isinstance(results.get("local_results"), list):
                        local_results = results.get("local_results")
                    elif isinstance(results.get("local_results"), dict):
                        local_results = results["local_results"].get("places", [])
                    elif "places_results" in results:
                        local_results = results["places_results"]

                    if local_results:
                        empresas = []
                        for empresa in local_results:
                            empresas.append({
                                "nicho": nicho,
                                "cidade": cidade,
                                "nome": empresa.get("title"),
                                "endereco": empresa.get("address"),
                                "telefone": empresa.get("phone"),
                                "website": empresa.get("website"),
                                "tipo": empresa.get("type"),
                                "nota": empresa.get("rating"),
                                "reviews": empresa.get("reviews"),
                                "Descricao": empresa.get("description"),
                                "Latitude": empresa.get("gps_coordinates", {}).get("latitude"),
                                "Longitude": empresa.get("gps_coordinates", {}).get("longitude"),
                            })
                        logging.info(f"✅ {len(empresas)} empresas encontradas com engine '{engine}'")
                        return empresas

                    else:
                        logging.warning(
                            f"⚠️ Nenhum resultado retornado ({engine}) para {nicho} em {cidade} (tentativa {attempt+1})"
                        )

            except Exception as e:
                logging.warning(f"⚠️ Erro ao chamar SerpAPI ({engine}) tentativa {attempt+1}: {e}")

            # Backoff exponencial
            delay = initial_delay * (2 ** attempt) + random.uniform(0.5, 1.5)
            logging.info(f"Aguardando {delay:.2f}s antes de tentar novamente...")
            time.sleep(delay)

        logging.warning(f"⚠️ Todas as tentativas com {engine} falharam, tentando engine alternativa...")

    logging.error(f"❌ Falha total para {nicho} em {cidade} (ambas as engines).")
    return []


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
                
                sleep_time = random.uniform(5, 9) 
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
    output_path = "results/csv/dados_empresas_googlemaps.csv"
    if os.path.exists(output_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"results/csv/dados_empresas_googlemaps_sub_{timestamp}.csv"
        os.rename(output_path, new_name)
        logging.info(f"Arquivo existente renomeado para {new_name}")

    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logging.info(f"\n✅ Dados salvos em '{output_path}' com {len(df)} registros.")

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
