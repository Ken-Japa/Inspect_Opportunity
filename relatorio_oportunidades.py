# Objetivo: gerar visualizações e insights automáticos do ranking de oportunidades

import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime

# ---------------------------------------------------
# 1. Ler dados
# ---------------------------------------------------
df = pd.read_csv("data/oportunidades.db.csv")

# Garantir que o score é numérico
df["score_oportunidade"] = pd.to_numeric(df["score_oportunidade"], errors="coerce")

# ---------------------------------------------------
# 2. Gráfico principal
# ---------------------------------------------------
output_dir = "results/"
output_filename = "grafico_oportunidades.png"
output_path = os.path.join(output_dir, output_filename)

# Cria o diretório de saída se não existir
os.makedirs(output_dir, exist_ok=True)

# Lógica para renomear arquivo existente com timestamp
if os.path.exists(output_path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(output_path)
    new_name = f"{base}_sub_{timestamp}{ext}"
    os.rename(output_path, new_name)
    print(f"Arquivo existente renomeado para: {new_name}")

plt.figure(figsize=(10, 6))
plt.barh(df["nicho"], df["score_oportunidade"], color="skyblue")
plt.xlabel("Score de Oportunidade")
plt.ylabel("Nicho")
plt.title("Ranking de Oportunidades Locais - " + df["cidade"].iloc[0])
plt.gca().invert_yaxis()  # Nichos com maior score no topo
for i, v in enumerate(df["score_oportunidade"]):
    plt.text(v + 0.01, i, f"{v:.2f}", va='center', fontsize=8)
plt.tight_layout()
plt.savefig(output_path, dpi=300)
plt.show()

# ---------------------------------------------------
# 3. Resumo automático de insights
# ---------------------------------------------------
media_score = df["score_oportunidade"].mean()
melhor_nicho = df.loc[df["score_oportunidade"].idxmax()]
alta_count = (df["classificacao"] == "Alta").sum()

print("\n📈 RESUMO DE INSIGHTS")
print(f"- Nichos analisados: {len(df)}")
print(f"- Score médio geral: {media_score:.2f}")
print(f"- Nichos com classificação 'Alta': {alta_count}")
print(f"- Nicho mais promissor: {melhor_nicho['nicho']} (Score {melhor_nicho['score_oportunidade']:.2f})")

# ---------------------------------------------------
# 4. Exportar apenas oportunidades 'Alta'
# ---------------------------------------------------
df_alta = df[df["classificacao"] == "Alta"]
if not df_alta.empty:
    df_alta.to_csv("nichos_alta_oportunidade.csv", index=False, encoding="utf-8-sig")
    print("\n🔥 Arquivo 'nichos_alta_oportunidade.csv' criado com os nichos mais promissores.")
else:
    print("\n⚠️ Nenhum nicho classificado como 'Alta' neste dataset.")
