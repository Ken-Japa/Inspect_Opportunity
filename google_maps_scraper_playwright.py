import asyncio
import random
import time
from playwright.async_api import async_playwright
import pandas as pd
import logging
import os

# Configuração de logging
log_file = "scraper_debug.log"
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def extract_business_data(page, card_locator, card_index):
    """
    Extrai nome, endereço, rating e reviews de um cartão de negócios.
    """
    nome = "N/A"
    endereco = "N/A"
    rating = "N/A"
    reviews = "N/A"

    logging.info(f"Tentando extrair dados para o cartão {card_index}...")
    # Log do conteúdo do card_locator para depuração
    card_content = await card_locator.text_content()
    logging.info(f"  Conteúdo do card_locator para o cartão {card_index}:\n{card_content[:500]}...") # Limita o log para não ser muito longo

    # Tentativas para extrair o nome
    name_selectors = [
        'a.hfpxzc', # Prioriza o seletor com aria-label
        'div[role="heading"]',
        'div[class*="fontHeadlineSmall"]',
        'div[data-section-id="title"]',
        'h2[data-test-id="section-result-title"]',
        'div[class*="GLOBAL_SCROLL_HANDLER"] h1'
    ]
    for selector in name_selectors:
        try:
            name_element = card_locator.locator(selector).first
            if await name_element.is_visible():
                if selector == 'a.hfpxzc':
                    nome = await name_element.get_attribute('aria-label')
                else:
                    nome = await name_element.text_content()
                logging.info(f"  Nome encontrado com seletor '{selector}': {nome}")
                break
            else:
                logging.info(f"  Cartão {card_index}: Seletor de nome '{selector}' encontrado, mas não visível.")
        except Exception as e:
            logging.info(f"  Cartão {card_index}: Seletor de nome '{selector}' não encontrou elemento ou erro: {e}")
    if nome == "N/A":
        logging.warning(f"  Cartão {card_index}: Nome não encontrado com os seletores padrão.")

    # Tentativas para extrair o endereço
    address_selectors = [
        'div[class*="address"]',
        'div:has-text("Endereço:")',
        'div.fontBodyMedium' # Pode ser um seletor genérico, precisa de mais contexto
    ]
    for selector in address_selectors:
        try:
            address_element = card_locator.locator(selector).first
            if await address_element.is_visible():
                endereco = await address_element.text_content()
                if "Endereço:" in endereco:
                    endereco = endereco.replace("Endereço:", "").strip()
                logging.info(f"  Endereço encontrado com seletor '{selector}': {endereco}")
                break
            else:
                logging.info(f"  Cartão {card_index}: Seletor de endereço '{selector}' encontrado, mas não visível.")
        except Exception as e:
            logging.info(f"  Cartão {card_index}: Seletor de endereço '{selector}' não encontrou elemento ou erro: {e}")
    if endereco == "N/A":
        logging.warning(f"  Cartão {card_index}: Endereço não encontrado com os seletores padrão.")

    # Tentativas para extrair o rating
    rating_selectors = [
        'span[aria-label*="estrelas"]',
        'span.fontBodyMedium > span[aria-label]'
    ]
    for selector in rating_selectors:
        try:
            rating_element = card_locator.locator(selector).first
            if await rating_element.is_visible():
                rating_text = await rating_element.text_content()
                if rating_text:
                    rating = rating_text.split(" ")[0].replace(",", ".")
                    logging.info(f"  Rating encontrado com seletor '{selector}': {rating}")
                break
            else:
                logging.info(f"  Cartão {card_index}: Seletor de rating '{selector}' encontrado, mas não visível.")
        except Exception as e:
            logging.info(f"  Cartão {card_index}: Seletor de rating '{selector}' não encontrou elemento ou erro: {e}")
    if rating == "N/A":
        logging.warning(f"  Cartão {card_index}: Rating não encontrado com os seletores padrão.")

    # Tentativas para extrair o número de reviews
    reviews_selectors = [
        'span:has-text("(")',
        'span.fontBodyMedium > span[aria-label]' # Pode conter reviews também
    ]
    for selector in reviews_selectors:
        try:
            reviews_element = card_locator.locator(selector).first
            if await reviews_element.is_visible():
                reviews_text = await reviews_element.text_content()
                if "(" in reviews_text and ")" in reviews_text:
                    reviews = reviews_text.split("(")[1].replace(")", "").replace(".", "")
                    logging.info(f"  Reviews encontrado com seletor '{selector}': {reviews}")
                break
            else:
                logging.info(f"  Cartão {card_index}: Seletor de reviews '{selector}' encontrado, mas não visível.")
        except Exception as e:
            logging.info(f"  Cartão {card_index}: Seletor de reviews '{selector}' não encontrou elemento ou erro: {e}")
    if reviews == "N/A":
        logging.warning(f"  Cartão {card_index}: Reviews não encontrado com os seletores padrão.")

    if nome == "N/A" and endereco == "N/A" and rating == "N/A" and reviews == "N/A":
        logging.warning(f"  ATENÇÃO: Nenhuma informação extraída para o cartão {card_index}.")
        # screenshot_path = f"debug_page_card_{card_index}.png"
        # await page.screenshot(path=screenshot_path, full_page=True)
        # logging.info(f"  Screenshot da página inteira salvo em {screenshot_path}")

    return {
        "Nome": nome,
        "Endereço": endereco,
        "Rating": rating,
        "Reviews": reviews
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
            await page.wait_for_timeout(random.randint(2000, 5000)) # Atraso aleatório após a navegação

            # Aceitar cookies, se o pop-up aparecer
            try:
                await page.click('button[aria-label="Aceitar tudo"]', timeout=5000)
                logging.info("Cookies aceitos.")
                await page.wait_for_timeout(random.randint(1000, 3000)) # Atraso aleatório após aceitar cookies
            except:
                logging.info("Pop-up de cookies não encontrado ou já aceito.")

            # Localizar a barra de pesquisa e digitar a consulta
            search_box_selector = 'input#searchboxinput'
            await page.fill(search_box_selector, f"{nicho} em {cidade}, Minas Gerais")
            await page.press(search_box_selector, "Enter")
            await page.wait_for_timeout(random.randint(3000, 6000)) # Atraso aleatório após a busca

            logging.info("Busca realizada. Aguardando resultados...")
            try:
                # Aumentar o timeout para dar mais tempo para a página carregar
                await page.wait_for_selector('div[role="main"]', timeout=30000) # Aumentado para 30 segundos
            except Exception as e:
                logging.error(f"Erro ao aguardar o seletor de resultados: {e}")
                await page.screenshot(path="error_screenshot.png")
                logging.info("Captura de tela salva como error_screenshot.png para depuração.")
                return []

            # Salvar o HTML da página para depuração
            # with open("debug_page_content.html", "w", encoding="utf-8") as f:
                #f.write(await page.content())
            # logging.info("Conteúdo da página salvo em debug_page_content.html para depuração.")

            # await page.pause() # Removido para depuração manual

            # Encontrar a área de resultados rolável
            # Tentando um seletor mais robusto para a área de rolagem
            scrollable_element = page.locator('div[role="main"] div[aria-label*="Resultados"]').first
            if not await scrollable_element.is_visible():
                logging.error("Elemento rolável não encontrado ou não visível.")
                await page.screenshot(path="error_scrollable_element.png")
                return []

            empresas_encontradas = []
            page_count = 0
            max_pages = 3 # Limite de páginas para evitar loops infinitos durante a depuração

            while page_count < max_pages:
                logging.info(f"Processando página {page_count + 1}...")
                last_height = await scrollable_element.evaluate("element => element.scrollHeight")
                scroll_attempts = 0
                max_scroll_attempts = 5 # Limitar o número de rolagens por página

                while True: # Loop infinito para rolar até o fim
                    await scrollable_element.evaluate("element => element.scrollBy(0, element.scrollHeight)")
                    await page.wait_for_timeout(random.randint(2000, 4000)) # Espera aleatória para simular interação humana

                    new_height = await scrollable_element.evaluate("element => element.scrollHeight")

                    # Verificar se o texto de "fim da lista" apareceu
                    if await page.locator('text="Você chegou ao fim da lista."').is_visible():
                        logging.info("Texto 'Você chegou ao fim da lista.' encontrado. Parando a rolagem.")
                        break

                    if new_height == last_height:
                        logging.info("Fim da rolagem na página atual.")
                        break
                    last_height = new_height
                    scroll_attempts += 1
                    if scroll_attempts > 20: # Limite de tentativas para evitar loops infinitos
                        logging.warning("Limite de tentativas de rolagem atingido na página atual.")
                        break

                # Obter todos os cartões de negócios visíveis na página atual
                business_cards = await page.locator('div[role="article"]').all()
                if not business_cards:
                    business_cards = await page.locator('div[jsaction*="mouseover"]').all()

                logging.info(f"Empresas visíveis na página atual: {len(business_cards)}")

                # Extrair dados das empresas
                for i, card in enumerate(business_cards):
                    data = await extract_business_data(page, card, i)
                    empresas_encontradas.append(data)

                page_count += 1

                # Tentar encontrar e clicar no botão da próxima página
                try:
                    next_page_button = page.locator('button[aria-label*="Próxima página"]')
                    await next_page_button.wait_for(state='visible', timeout=10000) # Espera até 10 segundos para o botão ficar visível
                    if await next_page_button.is_enabled():
                        logging.info("Clicando no botão 'Próxima página'...")
                        await next_page_button.click()
                        await page.wait_for_timeout(random.randint(3000, 6000)) # Espera para carregar a próxima página
                    else:
                        logging.info("Botão 'Próxima página' encontrado, mas desabilitado. Fim da paginação.")
                        break
                except TimeoutError:
                    logging.info("Botão 'Próxima página' não encontrado dentro do tempo limite. Fim da paginação.")
                    break
                except Exception as e:
                    logging.error(f"Erro inesperado ao tentar paginar: {e}")
                    break

            return empresas_encontradas
        finally:
            await browser.close()
            logging.info("Navegador fechado.")
        return empresas_encontradas

if __name__ == "__main__":
    # Exemplo de uso
    nicho_exemplo = "advogado"
    cidade_exemplo = "Belo Horizonte"
    
    # Executa a função e imprime os resultados
    dados_empresas = asyncio.run(buscar_google_maps(nicho_exemplo, cidade_exemplo))
    df = pd.DataFrame(dados_empresas)
    print("\n--- Dados Coletados ---")
    print(df)

    # Salvar os dados em um arquivo CSV
    output_filename = f"google_maps_data_{nicho_exemplo}_{cidade_exemplo}.csv"
    df.to_csv(output_filename, index=False, encoding='utf-8')
    logging.info(f"Dados salvos em {output_filename}")
    print(f"\nDados salvos em {output_filename}")