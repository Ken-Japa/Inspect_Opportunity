import pandas as pd
import os
from datetime import datetime, timedelta

def analisar_oportunidades(caminho_diretorio_csv, caminho_db_csv, dias_cache=30):
    """
    Analisa os resultados de oportunidades a partir de múltiplos arquivos CSV em um diretório,
    calcula o SPOL (Score de Pontuação de Oportunidades Locais) e gera um DataFrame consolidado.
    Inclui lógica de cache para evitar reprocessamento de dados recentes.

    Args:
        caminho_diretorio_csv (str): Caminho para o diretório contendo os arquivos CSV de resultados do scraper.
        caminho_db_csv (str): Caminho para o arquivo CSV do banco de dados incremental (cache).
        dias_cache (int): Número de dias para considerar um dado como 'recente' no cache.

    Returns:
        pd.DataFrame: DataFrame consolidado com as oportunidades e o score SPOL.
    """
    df_cache = pd.DataFrame()
    if os.path.exists(caminho_db_csv):
        try:
            df_cache = pd.read_csv(caminho_db_csv)
            df_cache.columns = df_cache.columns.str.strip().str.lower() # Limpa nomes das colunas do cache
            df_cache['timestamp'] = pd.to_datetime(df_cache['timestamp'])
            print(f"Lido {len(df_cache)} registros do cache em: {caminho_db_csv}. Colunas do cache: {df_cache.columns.tolist()}")
        except Exception as e:
            print(f"Erro ao carregar ou processar o arquivo de cache {caminho_db_csv}: {e}")
            df_cache = pd.DataFrame() # Reseta o cache em caso de erro

    all_dfs = []
    for filename in os.listdir(caminho_diretorio_csv):
        if filename.endswith(".csv"):
            file_path = os.path.join(caminho_diretorio_csv, filename)
            try:
                df_novo = pd.read_csv(file_path)
                df_novo.columns = df_novo.columns.str.strip().str.lower() 
                print(f"Colunas do arquivo {filename} após limpeza: {df_novo.columns.tolist()}") 
                df_novo['origem_csv'] = filename # Adiciona a coluna origem_csv

                # Lógica de cache: verificar se já existe dado recente para nicho/cidade
                df_para_processar = pd.DataFrame()
                for index, row in df_novo.iterrows():
                    try:
                        nicho = row['nicho']
                        cidade = row['cidade']
                    except KeyError as ke:
                        print(f"KeyError ao acessar 'nicho' ou 'cidade' no arquivo {filename} na linha {index}: {ke}. Colunas disponíveis no df_novo: {df_novo.columns.tolist()}")
                        continue # Pula para a próxima linha se 'nicho' ou 'cidade' não forem encontrados

                    # Assume que o dado não é recente por padrão
                    is_recent_in_cache = False
                    if not df_cache.empty:
                        # Verifica se há dados recentes no cache para este nicho e cidade
                        dados_recentes_cache = df_cache[
                            (df_cache['nicho'] == nicho) &
                            (df_cache['cidade'] == cidade) &
                            (df_cache['timestamp'] > datetime.now() - timedelta(days=dias_cache))
                        ]
                        if not dados_recentes_cache.empty:
                            is_recent_in_cache = True

                    if not is_recent_in_cache:
                        # Se não há dados recentes no cache, adiciona para processamento
                        df_para_processar = pd.concat([df_para_processar, pd.DataFrame([row])], ignore_index=True)
                    else:
                        print(f"Pulando processamento para {nicho} em {cidade}: dados recentes encontrados no cache.")
                
                if not df_para_processar.empty:
                    all_dfs.append(df_para_processar)
                    print(f"Adicionado {len(df_para_processar)} registros do arquivo {filename} para processamento.")

            except Exception as e:
                print(f"Erro ao ler o arquivo {filename}: {e}")
                continue

    if not all_dfs:
        print(f"Nenhum arquivo CSV novo para processar ou todos os dados são recentes no cache: {caminho_diretorio_csv}")
        return pd.DataFrame()

    df_consolidado = pd.concat(all_dfs, ignore_index=True)
    print(f"Total de {len(df_consolidado)} novos registros consolidados de todos os CSVs para processamento.")

    # Limpeza e preparação dos dados
    df_consolidado['nota'] = pd.to_numeric(df_consolidado['nota'], errors='coerce').fillna(0)
    df_consolidado['reviews'] = pd.to_numeric(df_consolidado['reviews'], errors='coerce').fillna(0)
    df_consolidado['website_presente'] = df_consolidado['website'].notna().astype(int)

    # Cálculo da concorrência (número de empresas por nicho e cidade)
    df_consolidado['concorrencia'] = df_consolidado.groupby(['nicho', 'cidade'])['nome'].transform('count')

    # Definição dos pesos para o cálculo do SPOL
    peso_concorrencia = 0.5  # Negativo
    peso_satisfacao = 0.7    # Negativo
    peso_reviews = 0.8       # Positivo
    peso_presenca_digital = 0.3 # Negativo (menos presença digital = mais oportunidade)
    peso_ticket_medio = 1.0  # Positivo (placeholder por enquanto)

    # Placeholder para ticket_estimado (assumindo um valor médio ou a ser preenchido)
    df_consolidado['ticket_estimado'] = 100 # Valor padrão, ajustar conforme dados reais

    # Cálculo do SPOL
    # A fórmula é ajustada para que um score mais alto signifique mais oportunidade
    df_consolidado['score_spol'] = (
        (df_consolidado['reviews'] * peso_reviews) -
        (df_consolidado['nota'] * peso_satisfacao) -
        (df_consolidado['concorrencia'] * peso_concorrencia) -
        (df_consolidado['website_presente'] * peso_presenca_digital) +
        (df_consolidado['ticket_estimado'] * peso_ticket_medio)
    )

    # Adiciona o timestamp atual
    df_consolidado['timestamp'] = datetime.now()

    # Selecionar e renomear colunas para o DataFrame consolidado final
    df_final = df_consolidado[[
        'cidade', 'nicho', 'nome', 'score_spol', 'ticket_estimado',
        'website_presente', 'nota', 'reviews', 'concorrencia', 'timestamp', 'origem_csv'
    ]].rename(columns={
        'nome': 'empresas',
        'website_presente': 'presenca_digital',
        'nota': 'nota_media'
    })

    return df_final

def salvar_resultados_incremental(df_novos_resultados, caminho_db_csv):
    """
    Salva os novos resultados de oportunidades incrementalmente em um arquivo CSV.
    Se o arquivo já existir, os novos resultados são anexados.

    Args:
        df_novos_resultados (pd.DataFrame): DataFrame com os novos resultados a serem salvos.
        caminho_db_csv (str): Caminho para o arquivo CSV do banco de dados incremental.
    """
    if df_novos_resultados.empty:
        print("Nenhum novo resultado para salvar incrementalmente.")
        return

    if os.path.exists(caminho_db_csv):
        df_existente = pd.read_csv(caminho_db_csv)
        df_existente['timestamp'] = pd.to_datetime(df_existente['timestamp'])
        df_combinado = pd.concat([df_existente, df_novos_resultados], ignore_index=True)
        # Remover duplicatas, mantendo a entrada mais recente (baseado em nicho, cidade, empresas e timestamp)
        df_combinado.sort_values(by='timestamp', ascending=True, inplace=True)
        df_combinado.drop_duplicates(subset=['cidade', 'nicho', 'empresas'], keep='last', inplace=True)
        print(f"Resultados anexados e salvos incrementalmente em: {caminho_db_csv}")
    else:
        df_combinado = df_novos_resultados
        print(f"Arquivo de banco de dados criado em: {caminho_db_csv}")

    df_combinado.to_csv(caminho_db_csv, index=False)


def gerar_relatorio_top_oportunidades(df_oportunidades, num_top=10):
    """
    Gera um relatório das top N oportunidades com base no score SPOL.

    Args:
        df_oportunidades (pd.DataFrame): DataFrame consolidado com as oportunidades e o score SPOL.
        num_top (int): Número de top oportunidades a serem exibidas no relatório.
    """
    if df_oportunidades.empty:
        print("Não há oportunidades para gerar o relatório.")
        return

    df_top_oportunidades = df_oportunidades.sort_values(by='score_spol', ascending=False).head(num_top)
    print(f"\n--- Top {num_top} Oportunidades (Relatório) ---")
    print(df_top_oportunidades.to_string(index=False))
    print("-----------------------------------------")

if __name__ == "__main__":
    # Exemplo de uso (ajuste o caminho conforme necessário)
    caminho_diretorio_csv_exemplo = r"c:\Users\Ken\Desktop\Projeto\Oportunidades Empresa\Trae - Negocios\results\csv"
    caminho_db_csv_exemplo = r"c:\Users\Ken\Desktop\Projeto\Oportunidades Empresa\Trae - Negocios\db_oportunidades.csv"

    df_oportunidades = analisar_oportunidades(caminho_diretorio_csv_exemplo, caminho_db_csv_exemplo)

    if not df_oportunidades.empty:
        print("\nDataFrame de Oportunidades (amostra com SPOL):")
        print(df_oportunidades.head())

        salvar_resultados_incremental(df_oportunidades, caminho_db_csv_exemplo)

    # Carrega o DataFrame completo do cache para gerar o relatório
    if os.path.exists(caminho_db_csv_exemplo):
        df_final_para_relatorio = pd.read_csv(caminho_db_csv_exemplo)
        gerar_relatorio_top_oportunidades(df_final_para_relatorio, num_top=10)
    else:
        print("Não foi possível gerar o relatório: arquivo de cache não encontrado.")