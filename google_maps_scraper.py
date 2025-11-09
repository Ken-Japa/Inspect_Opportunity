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
import argparse

PAGE_SIZE = 20

# Configuração do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def carregar_lista_de_arquivo(nome_arquivo, tipo):
    """Carrega uma lista de um arquivo CSV ou JSON."""
    caminho_csv = os.path.join(os.getcwd(), "input", f"{nome_arquivo}.csv")
    caminho_json = os.path.join(os.getcwd(), "input", f"{nome_arquivo}.json")

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
load_dotenv() 
API_KEY = os.getenv("SERPAPI_API_KEY")
if not API_KEY:
    raise ValueError("A variável de ambiente SERPAPI_API_KEY não está definida.")

# ----------------------------------------
# FUNÇÃO PRINCIPAL
# ----------------------------------------
def buscar_empresas(nicho: str, cidade: str, max_pages: int = 3) -> list[dict]:
    """Busca empresas no Google Maps usando a SerpAPI com paginação."""
    logging.info(f"🔍 Buscando: {nicho} em {cidade}...")
    engines = ["google_local", "google_maps"]
    max_retries = 2
    initial_delay = 1
    all_empresas = []

    for engine in engines:
        logging.info(f"🧭 Usando engine: {engine}")
        should_stop_pagination = False 
        for page in range(max_pages):
            if should_stop_pagination:
                break
            start_offset = page * 20 
            params = {
                "engine": engine,
                "q": f"{nicho} em {cidade}, Rio de Janeiro",
                "hl": "pt",
                "gl": "br",
                "api_key": API_KEY,
                "start": start_offset,
                "num": 20,
            }

            for attempt in range(max_retries):
                try:
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    
                    if "error" in results:
                        logging.warning(
                            f"⚠️ Erro da SerpAPI ({engine}, página {page+1}) para {nicho}: {results['error']} (tentativa {attempt+1}/{max_retries})"
                        )
                    else:
                        local_results = []
                        if isinstance(results.get("local_results"), list):
                            local_results = results.get("local_results")
                        elif isinstance(results.get("local_results"), dict):
                            local_results = results["local_results"].get("places", [])
                        elif "places_results" in results:
                            local_results = results["places_results"]

                        if local_results:
                            empresas_pagina = []
                            for empresa in local_results:
                                nome_empresa = empresa.get("title")
                                if not nome_empresa:
                                    logging.warning(f"⚠️ Empresa sem nome encontrada e ignorada em {cidade}, nicho {nicho} (página {page+1}).")
                                    continue

                                nota_empresa = pd.to_numeric(empresa.get("rating"), errors="coerce")
                                reviews_empresa = pd.to_numeric(empresa.get("reviews"), errors="coerce")

                                empresas_pagina.append({
                                    "nicho": nicho,
                                    "cidade": cidade,
                                    "nome": nome_empresa,
                                    "endereco": empresa.get("address"),
                                    "telefone": empresa.get("phone"),
                                    "website": empresa.get("website"),
                                    "tipo": empresa.get("type"),
                                    "nota": nota_empresa if not pd.isna(nota_empresa) else 0,
                                    "reviews": reviews_empresa if not pd.isna(reviews_empresa) else 0,
                                    "Descricao": empresa.get("description"),
                                    "Latitude": empresa.get("gps_coordinates", {}).get("latitude"),
                                    "Longitude": empresa.get("gps_coordinates", {}).get("longitude"),
                                })
                            all_empresas.extend(empresas_pagina)
                            logging.info(f"✅ {len(empresas_pagina)} empresas encontradas com engine '{engine}' na página {page+1}.")
                            
                            if len(empresas_pagina) < PAGE_SIZE:
                                logging.info(f"Menos de {PAGE_SIZE} resultados na página {page+1}. Assumindo que não há mais páginas para o engine '{engine}'.")
                                should_stop_pagination = True
                                break
                            if not search.get_dict().get("serpapi_pagination", {}).get("next_link") and not search.get_dict().get("serpapi_pagination", {}).get("next"):
                                logging.info(f"Fim da paginação para {nicho} em {cidade} com engine '{engine}'.")
                                should_stop_pagination = True
                                break
                            else:
                                sleep_time_page = random.uniform(1, 3)
                                logging.info(f"Aguardando {sleep_time_page:.2f}s antes da próxima página...")
                                time.sleep(sleep_time_page)
                            break 
                        else:
                            logging.warning(
                                f"⚠️ Nenhum resultado retornado ({engine}, página {page+1}) para {nicho} em {cidade} (tentativa {attempt+1})"
                            )
                            break 

                except Exception as e:
                    logging.warning(f"⚠️ Erro ao chamar SerpAPI ({engine}, página {page+1}) tentativa {attempt+1}: {e}")

                # Backoff exponencial
                delay = initial_delay * (2 ** attempt) + random.uniform(0.5, 1.5)
                logging.info(f"Aguardando {delay:.2f}s antes de tentar novamente...")
                time.sleep(delay)
            else:
                logging.warning(f"⚠️ Todas as tentativas com {engine} falharam para a página {page+1}, tentando engine alternativa...")
                break 

        if all_empresas: 
            break

    if not all_empresas:
        logging.error(f"❌ Falha total para {nicho} em {cidade} (ambas as engines e todas as páginas).")
    return all_empresas


# ----------------------------------------
# EXECUÇÃO PRINCIPAL
# ----------------------------------------
def main():
    """
    Função principal para orquestrar a busca de empresas no Google Maps.
    Carrega cidades e nichos, itera sobre eles, busca empresas e salva os dados.
    """
    parser = argparse.ArgumentParser(description="Scraper de empresas do Google Maps.")
    parser.add_argument("--mode", type=str, default="default",
                        help="Modo de execução: 'default' para cidades.csv e nichos.csv, 'expansao' para melhores_oportunidades.db.csv e cidades_vizinhas.csv.")
    args = parser.parse_args()

    if args.mode == "expansao":
        cidades = carregar_lista_de_arquivo("cidades_vizinhas", "cidades vizinhas")
        nichos_df = pd.read_csv(os.path.join(os.getcwd(), "data", "melhores_oportunidades.db.csv"))
        nichos = nichos_df["nicho"].tolist()
        logging.info("Modo 'expansao' ativado. Carregando nichos de melhores_oportunidades.db.csv e cidades de cidades_vizinhas.csv.")
    else:
        cidades = carregar_lista_de_arquivo("cidades", "cidades")
        nichos = carregar_lista_de_arquivo("nichos", "nichos")
        logging.info("Modo 'default' ativado. Carregando nichos de nichos.csv e cidades de cidades.csv.")

    if not cidades:
        logging.error("❌ A lista de cidades está vazia. Verifique o arquivo de cidades.")
        return

    if not nichos:
        logging.error("❌ A lista de nichos está vazia. Verifique o arquivo de nichos.")
        return

    todas_empresas = []

    for cidade in cidades:
        for nicho in nichos:
            try:
                logging.info(f"Iniciando busca para o nicho '{nicho}' na cidade '{cidade}'.")
                dados = buscar_empresas(nicho, cidade, max_pages=5)
                todas_empresas.extend(dados)
                
                sleep_time = random.uniform(5, 9) 
                logging.info(f"Aguardando {sleep_time:.2f} segundos antes da próxima requisição para evitar bloqueio...")
                time.sleep(sleep_time)
            except Exception as e:
                logging.error(f"⚠️ Erro ao buscar empresas para o nicho '{nicho}' na cidade '{cidade}': {e}")

    df = pd.DataFrame(todas_empresas)

    if not df.empty:
        for col in ["nota", "reviews"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Salvar CSV
        if args.mode == "expansao":
            for cidade_salvar in df["cidade"].unique():
                for nicho_salvar in df["nicho"].unique():
                    df_filtrado = df[(df["cidade"] == cidade_salvar) & (df["nicho"] == nicho_salvar)]
                    if not df_filtrado.empty:
                        nicho_sanitizado = nicho_salvar.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
                        cidade_sanitizada = cidade_salvar.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
                        output_filename = f"dados_empresas_{nicho_sanitizado}_{cidade_sanitizada}.csv"
                        output_path = os.path.join(os.getcwd(), "results", "csv", output_filename)
                        df_filtrado.to_csv(output_path, index=False, encoding="utf-8-sig")
                        logging.info(f"\n✅ Dados para '{nicho_salvar}' em '{cidade_salvar}' salvos em '{output_path}' com {len(df_filtrado)} registros.")
        else:
            output_path = os.path.join(os.getcwd(), "results", "csv", "dados_empresas_googlemaps.csv")
            if os.path.exists(output_path):
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = os.path.join(os.getcwd(), "results", "csv", f"dados_empresas_googlemaps_sub_{timestamp}.csv")
                os.rename(output_path, new_name)
                logging.info(f"Arquivo existente renomeado para {new_name}")

            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            logging.info(f"\n✅ Dados salvos em '{output_path}' com {len(df)} registros.")

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
    else:
        logging.warning("Nenhum dado de empresa foi coletado. Nenhum arquivo CSV será gerado.")

if __name__ == "__main__":
    main()
