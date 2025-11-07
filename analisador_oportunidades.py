# ===============================================================
# analisador_oportunidades.py
# Objetivo: analisar dados do scraper e gerar ranking de oportunidades
# ===============================================================

import pandas as pd
import logging
import os
import datetime

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
    df["nota"] = pd.to_numeric(df.get("nota"), errors="coerce")
    df["reviews"] = pd.to_numeric(df.get("reviews"), errors="coerce")
    df = df.dropna(subset=["nome"])
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

    return round(max(0, min(score, 1)), 3)  # Normalizado entre 0 e 1


def classificar(score, limites):
    """Classifica o score em Alta, Média ou Baixa."""
    if score >= limites["alta"]:
        return "Alta"
    elif score >= limites["media"]:
        return "Média"
    return "Baixa"


def salvar_ranking(df, output_file):
    """Salva o resultado com versionamento automático."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    if os.path.exists(output_file):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{output_file.replace('.csv', '')}_sub_{timestamp}.csv"
        os.rename(output_file, new_name)
        logging.info(f"📂 Arquivo existente renomeado para: {new_name}")

    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    logging.info(f"✅ Ranking salvo em: {output_file}")


# ---------------------------------------------------
# 3. Execução principal
# ---------------------------------------------------
def main():
    input_file = "results/csv/dados_empresas_googlemaps.csv"
    output_file = "results/csv/ranking_oportunidades.csv"

    pesos = {"demanda": 0.4, "concorrencia": 0.3, "satisfacao": 0.3}
    limites = {"alta": 0.66, "media": 0.4}

    df = carregar_dados(input_file)
    if df.empty:
        logging.warning("⚠️ Nenhum dado para processar.")
        return

    resumo = gerar_metricas(df)
    resumo["score_oportunidade"] = resumo.apply(lambda r: calcular_score(r, pesos), axis=1)
    resumo["classificacao"] = resumo["score_oportunidade"].apply(lambda s: classificar(s, limites))

    # Ordenar e salvar
    resumo = resumo.sort_values("score_oportunidade", ascending=False)
    salvar_ranking(resumo, output_file)

    # Log de insights
    media = resumo["score_oportunidade"].mean()
    top = resumo.iloc[0]
    altas = (resumo["classificacao"] == "Alta").sum()

    logging.info("\n📊 RESUMO DE INSIGHTS")
    logging.info(f"- Nichos analisados: {len(resumo)}")
    logging.info(f"- Score médio geral: {media:.2f}")
    logging.info(f"- Nichos 'Alta': {altas}")
    logging.info(f"- Melhor nicho: {top['nicho']} (Score {top['score_oportunidade']:.2f})")

    if altas == 0:
        logging.warning("⚠️ Nenhum nicho com score alto neste dataset.")


if __name__ == "__main__":
    main()
