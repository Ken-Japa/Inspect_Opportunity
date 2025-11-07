# consolidar.py
# Este script consolida e organiza os dados de oportunidades e empresas.

import pandas as pd
import os
import glob
import time
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configurações --- #
LIMITE_SCORE = 0.63

# --- Funções de Consolidação --- #

def consolidar_dados_empresas_googlemaps(results_path, consolidated_path):
    """
    Consolida todos os arquivos dados_empresas_googlemaps_sub_*.csv em um único arquivo master.
    Realiza deduplicação com base em "nome", "cidade" e "nicho".
    """
    print("Consolidando dados_empresas_googlemaps...")
    all_files = glob.glob(os.path.join(results_path, "csv", "dados_empresas_googlemaps_sub_*.csv"))
    
    if not all_files:
        print("Nenhum arquivo dados_empresas_googlemaps_sub_*.csv encontrado para consolidar.")
        return pd.DataFrame()

    df_list = []
    for f in all_files:
        df = pd.read_csv(f)
        df_list.append(df)
    
    if not df_list:
        return pd.DataFrame()

    df_master = pd.concat(df_list, ignore_index=True)
    df_master.drop_duplicates(subset=["nome", "cidade", "nicho"], inplace=True)
    
    output_path = os.path.join(consolidated_path, "dados_empresas_googlemaps_master.csv")
    os.makedirs(consolidated_path, exist_ok=True)
    df_master.to_csv(output_path, index=False)
    print(f"Dados consolidados salvos em: {output_path}")
    return df_master

def criar_nichos_especificos(df_oportunidades, df_empresas_master, consolidated_path):
    """
    Cria arquivos CSV específicos para nichos com score de oportunidade acima do limite.
    """
    print("Criando arquivos específicos por nicho...")
    especificos_path = os.path.join(consolidated_path, "especificos")
    os.makedirs(especificos_path, exist_ok=True)

    nichos_interessantes = df_oportunidades[df_oportunidades["score_oportunidade"] > LIMITE_SCORE]["nicho"].unique()

    for nicho in nichos_interessantes:
        df_nicho = df_empresas_master[df_empresas_master["nicho"] == nicho]
        # Limpar o nome do nicho para usar como nome de arquivo
        nicho_filename = nicho.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "").replace("*", "").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "")
        output_path = os.path.join(especificos_path, f"{nicho_filename}_empresas_googlemaps.csv")
        df_nicho.to_csv(output_path, index=False)
        print(f"Arquivo específico para nicho '{nicho}' salvo em: {output_path}")

# --- Funções de Limpeza --- #
def limpar_arquivos_antigos(results_path):
    """
    Deleta arquivos antigos de ranking_oportunidades e gráficos_oportunidades_sub.
    """
    print("Iniciando limpeza de arquivos antigos...")
    # Deletar ranking_oportunidades
    ranking_files = glob.glob(os.path.join(results_path, "csv", "ranking_oportunidades_sub_*.csv"))
    for f in ranking_files:
        try:
            os.remove(f)
            print(f"Arquivo deletado: {f}")
        except OSError as e:
            print(f"Erro ao deletar arquivo {f}: {e}")
            
    #Deletar dados_empresas_googlemaps_sub.csv
    dados_empresas = glob.glob(os.path.join(results_path, "csv", "dados_empresas_googlemaps_sub_*.csv"))
    for f in dados_empresas:
        try:
            os.remove(f)
            print(f"Arquivo deletado: {f}")
        except OSError as e:
            print(f"Erro ao deletar arquivo {f}: {e}")

    # Deletar grafico_oportunidades_sub_*.png
    grafico_sub_files = glob.glob(os.path.join(results_path, "grafico_oportunidades_sub_*.png"))
    for f in grafico_sub_files:
        try:
            os.remove(f)
            print(f"Arquivo deletado: {f}")
        except OSError as e:
            print(f"Erro ao deletar arquivo {f}: {e}")
    print("Limpeza de arquivos antigos concluída.")

# --- Funções de Consolidação --- #

def organizar_oportunidades_db(data_path):
    """
    Organiza o oportunidades.db.csv por score e cria um arquivo com as melhores oportunidades.
    """
    print("Organizando oportunidades.db.csv e criando melhores_oportunidades.db.csv...")
    oportunidades_db_path = os.path.join(data_path, "oportunidades.db.csv")
    df_oportunidades = pd.read_csv(oportunidades_db_path)

    # Ordenar e salvar oportunidades.db.csv
    df_oportunidades_sorted = df_oportunidades.sort_values(by="score_oportunidade", ascending=False)
    df_oportunidades_sorted.to_csv(oportunidades_db_path, index=False)
    print(f"oportunidades.db.csv organizado por score e salvo em: {oportunidades_db_path}")

    # Criar melhores_oportunidades.db.csv
    df_melhores_oportunidades = df_oportunidades_sorted[df_oportunidades_sorted["score_oportunidade"] > LIMITE_SCORE]
    melhores_oportunidades_path = os.path.join(data_path, "melhores_oportunidades.db.csv") # Alterado para data_path
    df_melhores_oportunidades.to_csv(melhores_oportunidades_path, index=False)
    print(f"Melhores oportunidades salvas em: {melhores_oportunidades_path}")
    return df_oportunidades_sorted, df_melhores_oportunidades

def gerar_grafico_oportunidades(df_melhores_oportunidades, data_path): # Alterado para data_path
    """
    Gera um gráfico de barras das melhores oportunidades por nicho, com o score exibido nas barras.
    """
    print("Gerando gráfico de oportunidades...")
    if df_melhores_oportunidades.empty:
        print("Não há melhores oportunidades para gerar o gráfico.")
        return

    # Agrupar por nicho e calcular a média do score de oportunidade
    df_plot = df_melhores_oportunidades.groupby("nicho")["score_oportunidade"].mean().sort_values(ascending=False).head(10) # Top 10 nichos

    plt.figure(figsize=(12, 7))
    ax = sns.barplot(x=df_plot.values, y=df_plot.index, palette="viridis")
    plt.title("Top 10 Nichos com Maiores Scores de Oportunidade")
    plt.xlabel("Score de Oportunidade Médio")
    plt.ylabel("Nicho")

    # Adicionar o valor do score nas barras
    for p in ax.patches:
        width = p.get_width()
        plt.text(width + 0.01, p.get_y() + p.get_height() / 2,
                 f'{width:.3f}',
                 ha='left', va='center')

    plt.tight_layout()
    graph_output_path = os.path.join(data_path, "grafico_oportunidades.png") # Alterado para data_path
    plt.savefig(graph_output_path)
    print(f"Gráfico de oportunidades salvo em: {graph_output_path}")
    plt.close()

def registrar_log_consolidacao(data_path, num_arquivos_processados, tempo_execucao): # Alterado para data_path
    """
    Registra os metadados da consolidação em um arquivo log_consolidacao.csv.
    """
    print("Registrando log de consolidação...")
    log_file_path = os.path.join(data_path, "log_consolidacao.csv") # Alterado para data_path
    
    log_entry = {
        "timestamp_consolidacao": pd.Timestamp.now(),
        "num_arquivos_processados": num_arquivos_processados,
        "tempo_execucao_segundos": tempo_execucao
    }
    df_log = pd.DataFrame([log_entry])

    if os.path.exists(log_file_path):
        df_log.to_csv(log_file_path, mode='a', header=False, index=False)
    else:
        df_log.to_csv(log_file_path, mode='w', header=True, index=False)
    print(f"Log de consolidação salvo em: {log_file_path}")

# --- Função Principal --- #

def main():
    start_time = time.time()
    
    base_path = os.getcwd()
    data_path = os.path.join(base_path, "data")
    results_path = os.path.join(base_path, "results")
    consolidated_path = os.path.join(results_path, "consolidados")

    # Limpar arquivos antigos antes de consolidar
    limpar_arquivos_antigos(results_path)

    # 1. Consolidar dados_empresas_googlemaps
    df_empresas_master = consolidar_dados_empresas_googlemaps(results_path, consolidated_path)
    num_processed_files = len(glob.glob(os.path.join(results_path, "csv", "dados_empresas_googlemaps_sub_*.csv")))

    # 2. Organizar oportunidades.db.csv e criar melhores_oportunidades.db.csv
    df_oportunidades_sorted, df_melhores_oportunidades = organizar_oportunidades_db(data_path) # Alterado para data_path

    # 3. Criar arquivos específicos por nicho (se houver dados de empresas)
    if not df_empresas_master.empty:
        criar_nichos_especificos(df_oportunidades_sorted, df_empresas_master, consolidated_path)
    else:
        print("Não há dados de empresas para criar arquivos específicos por nicho.")

    # 4. Gerar representação visual
    gerar_grafico_oportunidades(df_melhores_oportunidades, data_path) # Alterado para data_path

    end_time = time.time()
    tempo_execucao = end_time - start_time
    print(f"Tempo total de execução: {tempo_execucao:.2f} segundos")

    # 5. Registrar log de consolidação
    registrar_log_consolidacao(data_path, num_processed_files, tempo_execucao) # Alterado para data_path

    print("Processo de consolidação concluído!")

if __name__ == "__main__":
    main()