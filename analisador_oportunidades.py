# ===============================================================
# analisador_oportunidades.py
# Objetivo: analisar dados do scraper e gerar ranking de oportunidades
# ===============================================================

import pandas as pd
import logging
import os
import datetime
import argparse

# ---------------------------------------------------
# 1. Configuração do logger
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# ---------------------------------------------------
# 2. Funções principais
# ---------------------------------------------------

def carregar_dados(input_file: str) -> pd.DataFrame:
    """Carrega e limpa os dados do CSV de entrada."""
    if not os.path.exists(input_file):
        logging.error(f"❌ Arquivo '{input_file}' não encontrado.")
        return pd.DataFrame()

    df = pd.read_csv(input_file)

    required_columns = ["cidade", "nicho", "nome", "nota", "reviews"]
    if not all(col in df.columns for col in required_columns):
        missing_cols = [col for col in required_columns if col not in df.columns]
        logging.error(f"❌ CSV de entrada '{input_file}' está faltando colunas obrigatórias: {', '.join(missing_cols)}.")
        return pd.DataFrame()

    df["nota"] = pd.to_numeric(df["nota"], errors="coerce").fillna(0)
    df["reviews"] = pd.to_numeric(df["reviews"], errors="coerce").fillna(0)
    df = df.dropna(subset=["nome"])

    if df.empty:
        logging.warning(f"⚠️ Após a limpeza, nenhum registro válido permaneceu em '{input_file}'.")
        return pd.DataFrame()
    logging.info(f"📥 {len(df)} registros carregados de '{input_file}'.")
    return df


def gerar_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Gera métricas agregadas por cidade e nicho."""
    resumo = (
        df.groupby(["cidade", "nicho"])
        .agg(
            empresas=("nome", "count"),
            nota_media=("nota", "mean"),
            total_reviews=("reviews", "sum"),
            pct_baixa_qualidade=("nota", lambda x: (x < 4).mean() * 100),
            pct_sem_reviews=("reviews", lambda x: (x.isna() | (x == 0)).mean() * 100),
        )
        .reset_index()
    )
    return resumo


def calcular_score(row, pesos):
    """Cálculo ajustado e normalizado do score de oportunidade."""
    demanda = min(row["total_reviews"] / 50, 1.0)
    concorrencia = 1 - min(row["empresas"] / 20, 1.0)
    satisfacao_inversa = (5 - (row["nota_media"] or 0)) / 5

    score = (
        (demanda * pesos["demanda"]) +
        (concorrencia * pesos["concorrencia"]) +
        (satisfacao_inversa * pesos["satisfacao"])
    )

    return round(max(0, min(score, 1)), 3)  

def classificar(score, limites):
    """Classifica o score em Alta, Média ou Baixa."""
    if score >= limites["alta"]:
        return "Alta"
    elif score >= limites["media"]:
        return "Média"
    return "Baixa"


def salvar_oportunidades_db(df_novo: pd.DataFrame, output_db_file: str):
    """Salva ou anexa o ranking de oportunidades ao arquivo mestre, removendo duplicatas e mantendo o mais recente."""
    os.makedirs(os.path.dirname(output_db_file), exist_ok=True)

    if os.path.exists(output_db_file):
        df_existente = pd.read_csv(output_db_file)
        df_combinado = pd.concat([df_existente, df_novo], ignore_index=True)
        # Remover duplicatas, mantendo a última entrada (mais recente)
        df_final = df_combinado.drop_duplicates(subset=["cidade", "nicho"], keep="last")
        logging.info(f"📊 {len(df_novo)} novas oportunidades combinadas com {len(df_existente)} existentes. Total após remoção de duplicatas: {len(df_final)}.")
    else:
        df_final = df_novo
        logging.info(f"🆕 Criando novo arquivo de oportunidades com {len(df_final)} registros.")

    df_final.to_csv(output_db_file, index=False, encoding="utf-8-sig")
    logging.info(f"✅ Oportunidades salvas/atualizadas em: {output_db_file}")


# ---------------------------------------------------
# 3. Execução principal
# ---------------------------------------------------
def main():
    """Função principal para analisar os dados de empresas e gerar o ranking de oportunidades."""
    parser = argparse.ArgumentParser(description="Analisador de oportunidades de negócios.")
    parser.add_argument("--input_dir", type=str, default=os.path.join(os.getcwd(), "results", "csv"),
                        help="Diretório contendo os arquivos CSV de dados de empresas.")
    args = parser.parse_args()

    output_db_file = os.path.join(os.getcwd(), "data", "oportunidades.db.csv")

    pesos = {"demanda": 0.4, "concorrencia": 0.3, "satisfacao": 0.3}
    limites = {"alta": 0.66, "media": 0.4}

    all_resumo_dfs = []

    # Iterar sobre os arquivos CSV no diretório de entrada
    for filename in os.listdir(args.input_dir):
        if filename.startswith("dados_empresas_") and filename.endswith(".csv"):
            input_file_path = os.path.join(args.input_dir, filename)
            logging.info(f"Processando arquivo: {filename}")
            df = carregar_dados(input_file_path)
            if df.empty:
                continue

            resumo = gerar_metricas(df)
            resumo["score_oportunidade"] = resumo.apply(lambda r: calcular_score(r, pesos), axis=1)
            resumo["classificacao"] = resumo["score_oportunidade"].apply(lambda s: classificar(s, limites))
            all_resumo_dfs.append(resumo)

    if not all_resumo_dfs:
        logging.warning("⚠️ Nenhum arquivo de dados de empresas encontrado para processar.")
        return

    final_resumo_df = pd.concat(all_resumo_dfs, ignore_index=True)
    final_resumo_df = final_resumo_df.sort_values("score_oportunidade", ascending=False)
    
    salvar_oportunidades_db(final_resumo_df, output_db_file)

    # Log de insights (apenas para o último conjunto de dados processado ou um resumo geral)
    if not final_resumo_df.empty:
        media = final_resumo_df["score_oportunidade"].mean()
        top = final_resumo_df.iloc[0]
        altas = (final_resumo_df["classificacao"] == "Alta").sum()

        logging.info("\n📊 RESUMO DE INSIGHTS GERAIS")
        logging.info(f"- Nichos analisados: {len(final_resumo_df)}")
        logging.info(f"- Score médio geral: {media:.2f}")
        logging.info(f"- Nichos 'Alta': {altas}")
        logging.info(f"- Melhor nicho: {top['nicho']} (Score {top['score_oportunidade']:.2f}) na cidade {top['cidade']}")

        if altas == 0:
            logging.warning("⚠️ Nenhum nicho com score alto neste dataset geral.")


if __name__ == "__main__":
    main()
