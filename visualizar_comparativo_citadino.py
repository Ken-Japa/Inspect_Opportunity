import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Garante que o diretório de imagens exista
output_image_dir = "data/imagens"
os.makedirs(output_image_dir, exist_ok=True)

# Carrega o relatório comparativo
df = pd.read_csv("data/relatorio_comparativo_multicitadino.csv")

# --- Gráfico 1: Mapa de Nichos - Consistência vs Score Médio ---
plt.figure(figsize=(14, 10)) # Increased figure size
sc = plt.scatter(
    df["Média do score"],
    df["Replicabilidade (%)"],
    c=df["Desvio padrão"],
    s=df["Nº de cidades analisadas"] * 50,
    cmap="viridis",
    alpha=0.8,
    edgecolors="black"
)

plt.colorbar(sc, label="Desvio padrão")
plt.xlabel("Média do Score")
plt.ylabel("Replicabilidade (%)")
plt.title("Mapa de Nichos - Consistência vs Score Médio")

# Adiciona rótulos para os top nichos para reduzir a sobreposição
# Sort by a combined metric to prioritize important niches for labeling
df_sorted_for_labels = df.sort_values(by=["Média do score", "Replicabilidade (%)"], ascending=[False, False])
for i, row in df_sorted_for_labels.head(15).iterrows(): # Label top 15 niches
    plt.text(row["Média do score"] + 0.005, row["Replicabilidade (%)"] + 0.5, row["Nicho"], fontsize=8, ha='left', va='center')

plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(output_image_dir, "mapa_nichos_consistencia_score.png"))
plt.close()

# --- Gráfico 2: Top Nichos Replicáveis (Score > 0.63) ---
df_top = df[df["Média do score"] > 0.63].sort_values(by="Média do score", ascending=True)

if not df_top.empty:
    plt.figure(figsize=(10, 7))
    plt.barh(df_top["Nicho"], df_top["Média do score"], color="lightseagreen")
    for i, v in enumerate(df_top["Média do score"]):
        plt.text(v + 0.005, i, f"{v:.2f}", va="center", fontsize=9)

    plt.xlabel("Média do Score")
    plt.title("Top Nichos Replicáveis (Score > 0.63)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_image_dir, "top_nichos_replicaveis.png"))
    plt.close()
else:
    print("Nenhum nicho encontrado com Média do score > 0.63 para o gráfico de top nichos.")

# --- Gráfico 3: Distribuição de Scores por Nicho e Cidade (Heatmap) ---
# Supondo que 'oportunidades.db.csv' tenha as colunas 'cidade', 'nicho', 'score_oportunidade'
df_raw = pd.read_csv("data/oportunidades.db.csv")

pivot = df_raw.pivot_table(index="nicho", columns="cidade", values="score_oportunidade", aggfunc="mean")

if not pivot.empty:
    plt.figure(figsize=(14, 10))
    sns.heatmap(pivot, cmap="YlGnBu", annot=True, fmt=".2f", linewidths=.5)
    plt.title("Distribuição de Scores por Nicho e Cidade")
    plt.tight_layout()
    plt.savefig(os.path.join(output_image_dir, "heatmap_scores_nicho_cidade.png"))
    plt.close()
else:
    print("Nenhum dado encontrado em oportunidades.db.csv para gerar o heatmap.")

# --- Gráfico 4: Tabela Comparativa com Cores ---
if not df.empty:
    fig, ax = plt.subplots(figsize=(18, len(df) * 0.5 + 1))
    ax.axis('off') # Hide axes

    # Prepare data for table, format numerical columns
    df_display = df.copy()
    for col in ["Nº de cidades analisadas", "Média do score", "Desvio padrão", "Replicabilidade (%)"]:
        if df_display[col].dtype == 'float64':
            df_display[col] = df_display[col].map('{:.2f}'.format)
        else:
            df_display[col] = df_display[col].astype(str)

    table = ax.table(cellText=df_display.values,
                     colLabels=df_display.columns,
                     loc='center',
                     cellLoc='center')

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.auto_set_column_width(col=list(range(len(df_display.columns))))

    # Apply colors to numerical columns
    cmap_score = plt.cm.YlGn # Colormap for Média do score (higher is better)
    cmap_replicability = plt.cm.Greens # Colormap for Replicabilidade (%) (higher is better)
    cmap_cities = plt.cm.Blues # Colormap for Nº de cidades analisadas (higher is better)
    cmap_std_dev = plt.cm.Oranges_r # Colormap for Desvio padrão (lower is better, so _r for reversed)

    for i in range(len(df)):
        for j in range(len(df.columns)):
            col_name = df.columns[j]
            cell = table[(i + 1, j)] # +1 because of header row

            if col_name == "Média do score":
                val = df.iloc[i]["Média do score"]
                norm_val = (val - df["Média do score"].min()) / (df["Média do score"].max() - df["Média do score"].min()) if df["Média do score"].max() > df["Média do score"].min() else 0.5
                cell.set_facecolor(cmap_score(norm_val))
            elif col_name == "Replicabilidade (%)":
                val = df.iloc[i]["Replicabilidade (%)"]
                norm_val = (val - df["Replicabilidade (%)"].min()) / (df["Replicabilidade (%)"].max() - df["Replicabilidade (%)"].min()) if df["Replicabilidade (%)"].max() > df["Replicabilidade (%)"].min() else 0.5
                cell.set_facecolor(cmap_replicability(norm_val))
            elif col_name == "Nº de cidades analisadas":
                val = df.iloc[i]["Nº de cidades analisadas"]
                norm_val = (val - df["Nº de cidades analisadas"].min()) / (df["Nº de cidades analisadas"].max() - df["Nº de cidades analisadas"].min()) if df["Nº de cidades analisadas"].max() > df["Nº de cidades analisadas"].min() else 0.5
                cell.set_facecolor(cmap_cities(norm_val))
            elif col_name == "Desvio padrão":
                val = df.iloc[i]["Desvio padrão"]
                norm_val = (val - df["Desvio padrão"].min()) / (df["Desvio padrão"].max() - df["Desvio padrão"].min()) if df["Desvio padrão"].max() > df["Desvio padrão"].min() else 0.5
                cell.set_facecolor(cmap_std_dev(norm_val))

            cell._text.set_color('black') # Ensure text is visible

    plt.title("Relatório Comparativo de Nichos")
    plt.tight_layout()
    plt.savefig(os.path.join(output_image_dir, "tabela_comparativa_nichos.png"))
    plt.close()
else:
    print("Nenhum dado encontrado no relatório comparativo para gerar a tabela.")

print(f"Gráficos e tabelas salvos em: {output_image_dir}")