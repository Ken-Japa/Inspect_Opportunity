import pandas as pd
import os
from datetime import datetime

# Caminhos dos arquivos
CAMINHO_RANKING_OPORTUNIDADES = "results/csv/ranking_oportunidades.csv"
CAMINHO_DB_OPORTUNIDADES = "data/oportunidades.db.csv"
CAMINHO_HISTORICO_SCRAPERS = "data/historico_scrapers.csv"

def indexar_e_consolidar_oportunidades():
    """
    Lê o ranking_oportunidades.csv mais recente, adiciona ao banco global (oportunidades.db.csv),
    remove duplicatas (mantendo a entrada mais recente por cidade/nicho) e registra a execução.
    """
    print("Iniciando indexação e consolidação de oportunidades...")

    # 1. Ler o ranking_oportunidades.csv mais recente
    if not os.path.exists(CAMINHO_RANKING_OPORTUNIDADES):
        print(f"Erro: Arquivo {CAMINHO_RANKING_OPORTUNIDADES} não encontrado. Nenhuma nova oportunidade para indexar.")
        return

    df_ranking_recente = pd.read_csv(CAMINHO_RANKING_OPORTUNIDADES)
    
    # Adicionar timestamp de processamento
    df_ranking_recente['timestamp_processamento'] = datetime.now()

    # 2. Carregar o oportunidades.db.csv existente (se houver)
    if os.path.exists(CAMINHO_DB_OPORTUNIDADES):
        df_db_existente = pd.read_csv(CAMINHO_DB_OPORTUNIDADES)
        df_db_existente['timestamp_processamento'] = pd.to_datetime(df_db_existente['timestamp_processamento'])
        print(f"Banco de dados existente carregado com {len(df_db_existente)} entradas.")
    else:
        df_db_existente = pd.DataFrame()
        print("Banco de dados de oportunidades não encontrado. Criando um novo.")

    # 3. Adicionar os novos dados ao banco global e remover duplicatas
    df_consolidado = pd.concat([df_db_existente, df_ranking_recente], ignore_index=True)
    
    # Remover duplicatas, mantendo a entrada mais recente por 'nicho' e 'cidade'
    # Primeiro, garantir que 'nicho' e 'cidade' são strings para evitar erros de comparação
    df_consolidado['nicho'] = df_consolidado['nicho'].astype(str)
    df_consolidado['cidade'] = df_consolidado['cidade'].astype(str)

    df_consolidado.sort_values(by='timestamp_processamento', ascending=False, inplace=True)
    df_consolidado.drop_duplicates(subset=['nicho', 'cidade'], keep='first', inplace=True)
    df_consolidado.sort_values(by='timestamp_processamento', ascending=True, inplace=True) # Opcional: reordenar por data

    print(f"Banco de dados consolidado com {len(df_consolidado)} entradas após remover duplicatas.")

    # 4. Salvar o oportunidades.db.csv atualizado
    df_consolidado.to_csv(CAMINHO_DB_OPORTUNIDADES, index=False, encoding="utf-8-sig")
    print(f"Banco de dados de oportunidades atualizado salvo em {CAMINHO_DB_OPORTUNIDADES}")

    # 5. Registrar a execução no historico_scrapers.csv
    timestamp_execucao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cidades_processadas = df_ranking_recente['cidade'].unique().tolist()
    nichos_processados = df_ranking_recente['nicho'].unique().tolist()

    log_entry = {
        'timestamp': timestamp_execucao,
        'cidades': str(cidades_processadas),
        'nichos': str(nichos_processados),
        'novas_entradas': len(df_ranking_recente),
        'total_db': len(df_consolidado)
    }
    
    df_historico = pd.DataFrame([log_entry])

    if os.path.exists(CAMINHO_HISTORICO_SCRAPERS):
        df_historico_existente = pd.read_csv(CAMINHO_HISTORICO_SCRAPERS)
        df_historico = pd.concat([df_historico_existente, df_historico], ignore_index=True)
    
    df_historico.to_csv(CAMINHO_HISTORICO_SCRAPERS, index=False, encoding="utf-8-sig")
    print(f"Histórico de execução salvo em {CAMINHO_HISTORICO_SCRAPERS}")
    print("Indexação e consolidação concluídas.")

if __name__ == "__main__":
    indexar_e_consolidar_oportunidades()