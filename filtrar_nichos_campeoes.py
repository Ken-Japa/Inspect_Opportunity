import pandas as pd
import os
import re

def clean_niche_name_for_filename(niche_name):
    # Remove caracteres especiais e substitui espaços por underscores
    cleaned_name = re.sub(r'[^a-zA-Z0-9_\s]', '', niche_name)
    cleaned_name = cleaned_name.replace(' ', '_')
    return cleaned_name

def gerar_arquivos_nichos_campeoes():
    script_dir = os.path.dirname(__file__)
    data_dir = os.path.join(script_dir, 'data')
    results_dir = os.path.join(script_dir, 'results')
    nichos_campeoes_path = os.path.join(data_dir, 'nichos_campeoes.csv')
    dados_empresas_consolidado = os.path.join(results_dir, 'consolidados', 'dados_empresas_googlemaps_master.csv')
    cidades_vizinhas_dir = os.path.join(results_dir, 'cidadesVizinhas')
    output_nichos_campeoes_dir = os.path.join(results_dir, 'nichosCampeoes')
    debug_log_path = os.path.join(script_dir, 'debug_log.txt') # Caminho para o arquivo de log de depuração

    os.makedirs(output_nichos_campeoes_dir, exist_ok=True)

    print(f"Lendo nichos campeões de: {nichos_campeoes_path}")
    try:
        df_nichos_campeoes = pd.read_csv(nichos_campeoes_path)
        cleaned_champion_niches = df_nichos_campeoes['Nicho'].apply(clean_niche_name_for_filename).tolist()
        print(f"Nichos campeões lidos: {cleaned_champion_niches}")
    except FileNotFoundError:
        print(f"Erro: O arquivo {nichos_campeoes_path} não foi encontrado.")
        return

    todas_oportunidades = []

    # Abrir o arquivo de log de depuração
    with open(debug_log_path, 'w') as debug_log:
        debug_log.write("--- Início do Log de Depuração ---\n")

        print(f"Lendo banco de dados de oportunidades de: {dados_empresas_consolidado}")
        try:
            df_oportunidades_db = pd.read_csv(dados_empresas_consolidado)
            if 'nicho' in df_oportunidades_db.columns:
                df_oportunidades_db.loc[:, 'nicho_limpo'] = df_oportunidades_db['nicho'].apply(clean_niche_name_for_filename)
            
            # Debug: Imprimir nichos limpos únicos de df_oportunidades_db para o nicho alvo
            nicho_alvo_original = "Certificação de acessibilidade e laudos para edificações públicas"
            nicho_alvo_limpo = clean_niche_name_for_filename(nicho_alvo_original)
            
            df_oportunidades_db_nicho_alvo = df_oportunidades_db[df_oportunidades_db['nicho_limpo'] == nicho_alvo_limpo]
            if not df_oportunidades_db_nicho_alvo.empty:
                debug_log.write(f"[DEBUG] Nichos limpos únicos de df_oportunidades_db para '{nicho_alvo_original}': {df_oportunidades_db_nicho_alvo['nicho_limpo'].unique().tolist()}\n")
                debug_log.write(f"[DEBUG] Oportunidades de df_oportunidades_db para '{nicho_alvo_original}': {len(df_oportunidades_db_nicho_alvo)}\n")

            todas_oportunidades.append(df_oportunidades_db)
        except FileNotFoundError:
            print(f"Aviso: O arquivo {dados_empresas_consolidado} não foi encontrado. Continuando sem ele.")
        
        print(f"Buscando oportunidades em: {cidades_vizinhas_dir}")
        if os.path.exists(cidades_vizinhas_dir):
            for filename in os.listdir(cidades_vizinhas_dir):
                if filename.startswith('dados_empresas_') and filename.endswith('.csv'):
                    file_path = os.path.join(cidades_vizinhas_dir, filename)
                    
                    # Extrair o nome do nicho do arquivo de forma mais robusta
                    core_name = filename[len('dados_empresas_'):-len('.csv')]
                    core_name_cleaned = clean_niche_name_for_filename(core_name)
                    nicho_do_arquivo_cleaned = None
                    for champion_niche in cleaned_champion_niches:
                        if core_name_cleaned.startswith(champion_niche):
                            nicho_do_arquivo_cleaned = champion_niche
                            break

                    if nicho_do_arquivo_cleaned and nicho_do_arquivo_cleaned in cleaned_champion_niches:
                        try:
                            df_cidades_vizinhas = pd.read_csv(file_path)
                            # Adicionar coluna nicho_limpo
                            if 'nicho' in df_cidades_vizinhas.columns:
                                df_cidades_vizinhas.loc[:, 'nicho_limpo'] = df_cidades_vizinhas['nicho'].apply(clean_niche_name_for_filename)
                            
                            # Debug: Imprimir nichos limpos únicos de df_cidades_vizinhas para o nicho alvo
                            df_cidades_vizinhas_nicho_alvo = df_cidades_vizinhas[df_cidades_vizinhas['nicho_limpo'] == nicho_alvo_limpo]
                            if not df_cidades_vizinhas_nicho_alvo.empty:
                                debug_log.write(f"[DEBUG] Nichos limpos únicos de {filename} para '{nicho_alvo_original}': {df_cidades_vizinhas_nicho_alvo['nicho_limpo'].unique().tolist()}\n")
                                debug_log.write(f"[DEBUG] Oportunidades de {filename} para '{nicho_alvo_original}': {len(df_cidades_vizinhas_nicho_alvo)}\n")

                            todas_oportunidades.append(df_cidades_vizinhas)
                            print(f"Adicionado: {file_path}")
                        except pd.errors.EmptyDataError:
                            print(f"Aviso: O arquivo {filename} está vazio e foi ignorado.")
                        except Exception as e:
                            print(f"Erro ao ler o arquivo {filename}: {e}")

        if not todas_oportunidades:
            print("Nenhuma oportunidade encontrada para processar.")
            return

        df_todas_oportunidades = pd.concat(todas_oportunidades, ignore_index=True)
        
        # Remover duplicatas
        df_todas_oportunidades.drop_duplicates(subset=['nome', 'endereco', 'cidade'], inplace=True)
        total_oportunidades_unicas = len(df_todas_oportunidades)
        print(f"Total de oportunidades únicas encontradas: {total_oportunidades_unicas}")

        for nicho_campeao_limpo in cleaned_champion_niches:
            df_nicho = df_todas_oportunidades[df_todas_oportunidades['nicho_limpo'] == nicho_campeao_limpo]
            
            if not df_nicho.empty:
                output_filename = f"{nicho_campeao_limpo}.csv"
                output_path = os.path.join(output_nichos_campeoes_dir, output_filename)
                df_nicho.to_csv(output_path, index=False)
                print(f"Gerado: {output_path} com {len(df_nicho)} oportunidades.")
            else:
                print(f"Nenhuma oportunidade encontrada para o nicho: {nicho_campeao_limpo}")

        debug_log.write("--- Fim do Log de Depuração ---\n")

    print("Processo concluído.")

if __name__ == "__main__":
    gerar_arquivos_nichos_campeoes()