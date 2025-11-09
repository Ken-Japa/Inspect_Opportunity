import asyncio
import random
import time
from playwright.async_api import async_playwright
import pandas as pd
import logging
import os
import json
import pandas as pd
import argparse
import datetime

# Configuração de logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='scraper_debug.log', filemode='w')

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

async def extract_business_data(page, card_locator, card_index, nicho, cidade):
    """
    Extrai nome, endereço, rating e reviews de um cartão de negócios.
    """
    nome = "N/A"
    endereco = "N/A"
    rating = 0.0
    reviews = 0.0
    telefone = "N/A"
    website = "N/A"
    tipo = "N/A"
    descricao = "N/A"
    latitude = "N/A"
    longitude = "N/A"

    logging.info(f"Tentando extrair dados para o cartão {card_index}...")
    # Log do conteúdo do card_locator para depuração
    # card_content = await card_locator.evaluate('el => el.outerHTML')
    # logging.info(f"  Conteúdo completo do card_locator para o cartão {card_index}:\n{card_content}") 

    # Tentativas para extrair o nome
    try:
        nome = await card_locator.locator('div.qBF1Pd.fontHeadlineSmall').text_content() or \
               await card_locator.locator('a.hfpxzc').get_attribute('aria-label')
        logging.info(f"  Nome encontrado: {nome}")
    except Exception:
        nome = "N/A"
        logging.warning(f"  Cartão {card_index}: Nome não encontrado.")

    # Tentativas para extrair o endereço
    try:
        endereco = await card_locator.locator('div.W4Efsd > div:nth-child(1) > span:nth-child(3)').text_content()
        logging.info(f"  Endereço encontrado: {endereco}")
    except Exception:
        endereco = "N/A"
        logging.warning(f"  Cartão {card_index}: Endereço não encontrado.")

    # Tentativas para extrair o rating
    try:
        rating_text = await card_locator.locator('span.MW4etd').text_content()
        rating = float(rating_text.replace(',', '.')) if rating_text else 0.0
        logging.info(f"  Rating encontrado: {rating}")
    except Exception:
        rating = 0.0
        logging.warning(f"  Cartão {card_index}: Rating não encontrado.")

    # Tentativas para extrair o número de reviews
    try:
        reviews_text = await card_locator.locator('span.UY7F9').text_content()
        reviews = int(reviews_text.strip('()')) if reviews_text else 0
        logging.info(f"  Reviews encontrado: {reviews}")
    except Exception:
        reviews = 0
        logging.warning(f"  Cartão {card_index}: Reviews não encontrado.")

    # Tentativas para extrair o telefone
    try:
        telefone = await card_locator.locator('span.UsdlK').text_content()
        logging.info(f"  Telefone encontrado: {telefone}")
    except Exception:
        telefone = "N/A"
        logging.warning(f"  Cartão {card_index}: Telefone não encontrado.")

    # Tentativas para extrair o website
    try:
        website_locator = card_locator.locator('a.lcr4fd.S9kvJb[data-value="Website"]')
        website_href = await website_locator.get_attribute('href')
        if website_href and "/aclk?" not in website_href:
            website = website_href
        else:
            website = "N/A"
        logging.info(f"  Website encontrado: {website}")
    except Exception:
        website = "N/A"
        logging.warning(f"  Cartão {card_index}: Website não encontrado ou é um link de anúncio.")

    # Tentativas para extrair o tipo de negócio
    try:
        tipo = await card_locator.locator('div.W4Efsd > div:nth-child(1) > span:nth-child(1) > span:nth-child(1)').text_content()
        logging.info(f"  Tipo de negócio encontrado: {tipo}")
    except Exception:
        tipo = "N/A"
        logging.warning(f"  Cartão {card_index}: Tipo de negócio não encontrado.")


    if nome == "N/A" and endereco == "N/A" and rating == "N/A" and reviews == "N/A":
        logging.warning(f"  ATENÇÃO: Nenhuma informação extraída para o cartão {card_index}.")

    unique_id = hash(f"{nome}-{endereco}") # Gerar um ID único baseado no nome e endereço
    return {
        "nicho": nicho,
        "cidade": cidade,
        "Nome": nome,
        "Endereço": endereco,
        "Telefone": telefone,
        "Website": website,
        "Tipo": tipo,
        "Rating": rating,
        "Reviews": reviews,
        "Descricao": descricao,
        "Latitude": latitude,
        "Longitude": longitude,
        "unique_id": unique_id,
    }

async def buscar_google_maps(nicho: str, cidade: str):
    """
    Abre o Google Maps, realiza uma busca pelo nicho e cidade fornecidos e extrai informações das empresas.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # headless=False para ver o navegador em ação
        page = await browser.new_page()

        try:
            logging.info(f"Navegando para o Google Maps para buscar '{nicho}' em '{cidade}'...")
            await page.goto("https://www.google.com/maps")
            await page.wait_for_timeout(random.randint(2000, 5000))

            # Aceitar cookies, se o pop-up aparecer
            try:
                await page.click('button[aria-label="Aceitar tudo"]', timeout=5000)
                logging.info("Cookies aceitos.")
                await page.wait_for_timeout(random.randint(1000, 3000)) 
            except:
                logging.info("Pop-up de cookies não encontrado ou já aceito.")

            # Localizar a barra de pesquisa e digitar a cidade primeiro
            search_box_selector = 'input#searchboxinput'
            await page.fill(search_box_selector, cidade)
            await page.press(search_box_selector, "Enter")
            await page.wait_for_timeout(random.randint(3000, 6000)) 

            # Limpar a barra de pesquisa e digitar o nicho
            await page.fill(search_box_selector, nicho)
            await page.press(search_box_selector, "Enter")
            await page.wait_for_timeout(random.randint(3000, 6000))

            logging.info("Busca realizada. Aguardando resultados...")
            try:
                # Aumentar o timeout para dar mais tempo para a página carregar
                await page.wait_for_selector('div[role="main"]', timeout=30000) 
                await page.wait_for_timeout(random.randint(2000, 4000)) 
            except Exception as e:
                logging.error(f"Erro ao aguardar o seletor de resultados: {e}")
                await page.screenshot(path="error_screenshot.png")
                logging.info("Captura de tela salva como error_screenshot.png para depuração.")
                return []


            # Encontrar a área de resultados rolável
            scrollable_element = page.locator('div[role="main"] div[aria-label*="Resultados"]').first
            if not await scrollable_element.is_visible():
                logging.error("Elemento rolável não encontrado ou não visível.")
                await page.screenshot(path="error_scrollable_element.png")
                return []

            empresas_encontradas = []
            processed_business_ids = set() # Para armazenar IDs únicos de empresas já processadas
            last_scroll_height = -1
            no_new_businesses_count = 0
            max_no_new_businesses = 20 # Aumentar o limite de vezes que podemos não encontrar novas empresas

            while True:
                # Registrar o número de empresas visíveis antes da rolagem
                previous_business_cards_count = len(await page.locator('div.Nv2PK, div.TFQHme > div > div.Nv2PK').all())
                if not previous_business_cards_count:
                    previous_business_cards_count = len(await page.locator('div[role="article"]').all())
                logging.info(f"Empresas visíveis antes da rolagem: {previous_business_cards_count}")

                # Rolar para o final do elemento rolável em incrementos maiores
                await scrollable_element.evaluate("element => element.scrollBy(0, 1000)") # Rolar 1000px para baixo
                await page.wait_for_timeout(random.randint(3000, 7000)) # Esperar mais tempo para o conteúdo carregar


                current_scroll_height = await scrollable_element.evaluate("element => element.scrollHeight")

                # Obter todos os cartões de negócios visíveis na página atual
                business_cards = await page.locator('div.Nv2PK, div.TFQHme > div > div.Nv2PK').all()
                if not business_cards:
                    business_cards = await page.locator('div[role="article"]').all()
                logging.info(f"Empresas visíveis após rolagem: {len(business_cards)}")

                # Verificar se o número de empresas visíveis aumentou
                if len(business_cards) > previous_business_cards_count:
                    logging.info(f"Novas empresas visíveis detectadas: {len(business_cards) - previous_business_cards_count}")
                    no_new_businesses_count = 0 # Resetar o contador se novas empresas forem visíveis
                else:
                    no_new_businesses_count += 1
                    logging.info(f"Nenhuma nova empresa visível detectada. Contador: {no_new_businesses_count}/{max_no_new_businesses}")
                    if no_new_businesses_count >= max_no_new_businesses:
                        logging.info("Limite de não encontrar novas empresas visíveis atingido. Parando a rolagem.")
                        break

                new_businesses_found_in_scroll = False
                for i, card in enumerate(business_cards):
                    data = await extract_business_data(page, card, i, nicho, cidade)
                    if data["unique_id"] not in processed_business_ids:
                        empresas_encontradas.append(data)
                        processed_business_ids.add(data["unique_id"])
                        new_businesses_found_in_scroll = True
                        logging.info(f"  Cartão {i} (ID: {data["unique_id"]}) - NOVO. Adicionado.")
                    else:
                        logging.info(f"  Cartão {i} (ID: {data["unique_id"]}) - JÁ PROCESSADO. Ignorando.")

                # Verificar se o texto de "fim da lista" apareceu
                if await page.locator('text="Você chegou ao fim da lista."').is_visible():
                    logging.info("Texto 'Você chegou ao fim da lista.' encontrado. Parando a rolagem.")
                    break
                
                # Verificar se um botão "Mais resultados" ou similar apareceu
                more_results_button = page.locator('button[aria-label*="Mais resultados"]')
                if await more_results_button.is_visible():
                    logging.info("Botão 'Mais resultados' encontrado. Clicando para carregar mais.")
                    await more_results_button.click()
                    await page.wait_for_timeout(random.randint(3000, 6000)) # Esperar o carregamento
                    no_new_businesses_count = 0 # Resetar o contador após clicar no botão
                    continue # Continuar o loop para processar os novos resultados


                if not new_businesses_found_in_scroll and current_scroll_height == last_scroll_height:
                    logging.info("Fim da rolagem. Nenhuma nova altura de rolagem detectada. Parando a rolagem.")
                    break
                
                last_scroll_height = current_scroll_height

            return empresas_encontradas
        finally:
            await browser.close()
            logging.info("Navegador fechado.")
        return empresas_encontradas


def main():
    """
    Função principal para orquestrar a busca de empresas no Google Maps usando Playwright.
    Carrega cidades e nichos, itera sobre eles, busca empresas e salva os dados.
    """
    parser = argparse.ArgumentParser(description="Scraper de empresas do Google Maps usando Playwright.")
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
                dados = asyncio.run(buscar_google_maps(nicho, cidade))
                todas_empresas.extend(dados)
                
                sleep_time = random.uniform(5, 9) 
                logging.info(f"Aguardando {sleep_time:.2f} segundos antes da próxima requisição para evitar bloqueio...")
                time.sleep(sleep_time)
            except Exception as e:
                logging.error(f"⚠️ Erro ao buscar empresas para o nicho '{nicho}' na cidade '{cidade}': {e}")

    df = pd.DataFrame(todas_empresas)

    # Garante que as colunas estejam na ordem correta, adicionando as que podem estar faltando
    expected_columns = ["nicho", "cidade", "Nome", "Endereço", "Telefone", "Website", "Tipo", "Rating", "Reviews", "Descricao", "Latitude", "Longitude"]
    for col in expected_columns:
        if col not in df.columns:
            df[col] = "N/A"
    df = df[expected_columns]

    if not df.empty:
        for col in ["Rating", "Reviews"]:
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
            "Nome": "count",
            "Rating": "mean",
            "Reviews": "sum"
        }).rename(columns={
            "Nome": "quantidade_empresas",
            "Rating": "nota_media",
            "Reviews": "total_reviews"
        })

        logging.info("\n📊 Resumo inicial:")
        logging.info(resumo)
    else:
        logging.warning("Nenhum dado de empresa foi coletado. Nenhum arquivo CSV será gerado.")

if __name__ == "__main__":

    main()