# Autor: Ken
# Objetivo: analisar dados do scraper e gerar ranking de oportunidades

import pandas as pd
import logging
import sys
import argparse

# Configuração do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def carregar_dados(input_file):
    """
    Carrega os dados do arquivo CSV e realiza a limpeza inicial.
    Args:
        input_file (str): Caminho para o arquivo CSV de entrada.
    Returns:
        pd.DataFrame: DataFrame com os dados carregados e limpos.
    """
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        logging.error(f"❌ Erro: O arquivo '{input_file}' não foi encontrado. Certifique-se de que o scraper foi executado e o arquivo existe.")
        sys.exit(1)

    df["nota"] = pd.to_numeric(df["nota"], errors="coerce")
    df["reviews"] = pd.to_numeric(df["reviews"], errors="coerce")
    df = df.dropna(subset=["nome"])

    if df.empty:
        logging.error("❌ Erro: O DataFrame está vazio após a limpeza. Não há dados válidos para analisar.")
        sys.exit(1)
    return df

def gerar_metricas_mercado(df):
    """
    Calcula as métricas de mercado por cidade e nicho.
    Args:
        df (pd.DataFrame): DataFrame com os dados das empresas.
    Returns:
        pd.DataFrame: DataFrame resumido com as métricas de mercado.
    """
    resumo = (
        df.groupby(["cidade", "nicho"])
        .agg(
            empresas=("nome", "count"),
            nota_media=("nota", "mean"),
            total_reviews=("reviews", "sum"),
            pct_baixa_qualidade=("nota", lambda x: (x < 4).mean() * 100),
            sem_review=("reviews", lambda x: (x.isna() | (x == 0)).mean() * 100)
        )
        .reset_index()
    )
    return resumo

def calcular_score(row, demanda_peso, concorrencia_peso, satisfacao_peso):
    """
    Calcula o score de oportunidade para uma linha do DataFrame com pesos configuráveis.
    Args:
        row (pd.Series): Linha do DataFrame contendo as métricas de mercado.
        demanda_peso (float): Peso para o componente de demanda no cálculo do score.
        concorrencia_peso (float): Peso para o componente de concorrência no cálculo do score.
        satisfacao_peso (float): Peso para o componente de satisfação no cálculo do score.
    Returns:
        float: Score de oportunidade calculado.
    """
    demanda = min(row["total_reviews"] / 50, 1.0)
    concorrencia = 1 - min(row["empresas"] / 20, 1.0)
    satisfacao_inversa = (5 - (row["nota_media"] or 0)) / 5

    score = (demanda * demanda_peso) + (concorrencia * concorrencia_peso) + (satisfacao_inversa * satisfacao_peso)
    return round(score, 3)

def classificar(score, score_alto_limite, score_medio_limite):
    """
    Classifica o score de oportunidade em Alta, Média ou Baixa com limites configuráveis.
    Args:
        score (float): Score de oportunidade.
        score_alto_limite (float): Limite mínimo para classificação "Alta".
        score_medio_limite (float): Limite mínimo para classificação "Média".
    Returns:
        str: Classificação da oportunidade.
    """
    if score >= score_alto_limite:
        return "Alta"
    elif score >= score_medio_limite:
        return "Média"
    else:
        return "Baixa"

def salvar_resultados(resumo, output_file):
    """
    Salva o DataFrame de resultados em um arquivo CSV e loga um resumo.
    Args:
        resumo (pd.DataFrame): DataFrame com o ranking de oportunidades.
        output_file (str): Caminho para o arquivo CSV de saída.
    """
    resumo = resumo.sort_values("score_oportunidade", ascending=False)
    resumo.to_csv(output_file, index=False, encoding="utf-8-sig")

    logging.info(f"✅ Ranking gerado com sucesso: {output_file}")
    logging.info("\n📊 Resumo inicial:")
    logging.info(resumo)

def main():
    parser = argparse.ArgumentParser(description="Analisa dados de empresas e gera um ranking de oportunidades.")
    parser.add_argument("--input_file", type=str, default="dados_empresas_googlemaps.csv",
                        help="Caminho para o arquivo CSV de entrada gerado pelo scraper.")
    parser.add_argument("--output_file", type=str, default="ranking_oportunidades.csv",
                        help="Caminho para o arquivo CSV de saída com o ranking de oportunidades.")
    parser.add_argument("--demanda_peso", type=float, default=0.4,
                        help="Peso para o componente de demanda no cálculo do score.")
    parser.add_argument("--concorrencia_peso", type=float, default=0.3,
                        help="Peso para o componente de concorrência no cálculo do score.")
    parser.add_argument("--satisfacao_peso", type=float, default=0.3,
                        help="Peso para o componente de satisfação no cálculo do score.")
    parser.add_argument("--score_alto_limite", type=float, default=0.66,
                        help="Limite mínimo para classificação 'Alta' de oportunidade.")
    parser.add_argument("--score_medio_limite", type=float, default=0.4,
                        help="Limite mínimo para classificação 'Média' de oportunidade.")
    args = parser.parse_args()

    df = carregar_dados(args.input_file)
    resumo = gerar_metricas_mercado(df)

    resumo["score_oportunidade"] = resumo.apply(lambda row: calcular_score(row, args.demanda_peso, args.concorrencia_peso, args.satisfacao_peso), axis=1)
    resumo["classificacao"] = resumo["score_oportunidade"].apply(lambda score: classificar(score, args.score_alto_limite, args.score_medio_limite))

    salvar_resultados(resumo, args.output_file)

if __name__ == "__main__":
    main()
