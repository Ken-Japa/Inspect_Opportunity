# ===============================================================
# relatorio_comparativo_multicitadino.py
# Objetivo: Gerar um relatório comparativo de nichos entre múltiplas cidades.
# ===============================================================

import pandas as pd
import os
import logging

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

def carregar_oportunidades_db(db_file: str) -> pd.DataFrame:
    """Carrega o banco de dados consolidado de oportunidades."""
    if not os.path.exists(db_file):
        logging.error(f"❌ Arquivo do banco de dados '{db_file}' não encontrado.")
        return pd.DataFrame()
    
    df = pd.read_csv(db_file)
    logging.info(f"📥 {len(df)} registros carregados de '{db_file}'.")
    return df


def gerar_relatorio_comparativo(df: pd.DataFrame) -> pd.DataFrame:
    """Gera o relatório comparativo de nichos com métricas multicitadinas."""
    if df.empty:
        logging.warning("⚠️ DataFrame vazio. Não é possível gerar o relatório comparativo.")
        return pd.DataFrame()

    # Calcular métricas por nicho
    relatorio = df.groupby("nicho").agg(
        num_cidades_analisadas=("cidade", "nunique"),
        media_score=("score_oportunidade", "mean"),
        desvio_padrao=("score_oportunidade", "std"),
        num_cidades_alta_oportunidade=("classificacao", lambda x: (x == "Alta").sum())
    ).reset_index()

    # Calcular replicabilidade
    relatorio["replicabilidade_pct"] = (relatorio["num_cidades_alta_oportunidade"] / relatorio["num_cidades_analisadas"] * 100).round(2)
    relatorio["desvio_padrao"] = relatorio["desvio_padrao"].fillna(0).round(2) # Preencher NaN se houver apenas uma cidade
    relatorio["media_score"] = relatorio["media_score"].round(2)

    # Renomear colunas para o formato desejado
    relatorio = relatorio.rename(columns={
        "nicho": "Nicho",
        "num_cidades_analisadas": "Nº de cidades analisadas",
        "media_score": "Média do score",
        "desvio_padrao": "Desvio padrão",
        "replicabilidade_pct": "Replicabilidade (%)"
    })

    # Selecionar e ordenar colunas
    relatorio = relatorio[["Nicho", "Nº de cidades analisadas", "Média do score", "Desvio padrão", "Replicabilidade (%)"]]
    relatorio = relatorio.sort_values(by="Média do score", ascending=False)

    logging.info("📊 Relatório comparativo gerado com sucesso.")
    return relatorio


def salvar_relatorio(df_relatorio: pd.DataFrame, output_file: str):
    """Salva o relatório comparativo em um arquivo CSV."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_relatorio.to_csv(output_file, index=False, encoding="utf-8-sig")
    logging.info(f"✅ Relatório comparativo salvo em: {output_file}")

# ---------------------------------------------------
# 3. Execução principal
# ---------------------------------------------------
def main():
    """Função principal para gerar e salvar o relatório comparativo multicitadino."""
    db_file = os.path.join(os.getcwd(), "data", "oportunidades.db.csv")
    output_file = os.path.join(os.getcwd(), "data", "relatorio_comparativo_multicitadino.csv")

    df_oportunidades = carregar_oportunidades_db(db_file)
    if df_oportunidades.empty:
        logging.warning("⚠️ Não há dados no banco de oportunidades para gerar o relatório.")
        return

    df_relatorio = gerar_relatorio_comparativo(df_oportunidades)
    if not df_relatorio.empty:
        salvar_relatorio(df_relatorio, output_file)
    else:
        logging.warning("⚠️ O relatório comparativo está vazio. Nenhum arquivo será salvo.")

if __name__ == "__main__":
    main()