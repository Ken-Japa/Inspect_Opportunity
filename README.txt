# Projeto Boring Business Brasil 🧠🇧🇷
Automação e IA para encontrar, validar e monetizar negócios locais de alta margem.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=matplotlib&logoColor=white)
![SerpApi](https://img.shields.io/badge/SerpApi-000000?style=for-the-badge&logo=google&logoColor=white)
![python-dotenv](https://img.shields.io/badge/python--dotenv-F7DF1E?style=for-the-badge&logo=python&logoColor=black)

---

## 🎯 Objetivo Geral
Criar uma operação sustentável de geração de renda baseada em **identificação automatizada de nichos locais** e **monetização via lead generation ou operação direta**.

---

## 🚀 Evolução do Projeto e Tomada de Decisões
Este projeto evoluiu para otimizar a identificação e análise de oportunidades de negócios locais. As decisões foram tomadas com base na necessidade de automatizar, consolidar e visualizar dados de forma eficiente.

Inicialmente, o fluxo envolvia scripts separados para scraping, análise e indexação. No entanto, para melhorar a eficiência e reduzir a redundância, a lógica de remoção de duplicatas e consolidação de dados, que antes era responsabilidade do `indexador_oportunidades.py`, foi integrada diretamente ao `analisador_oportunidades.py`. Isso simplificou o pipeline e garantiu que os dados fossem processados e armazenados de forma otimizada em `oportunidades.db.csv`.

A introdução do `relatorio_comparativo_multicitadino.py` e do `visualizar_comparativo_citadino.py` foi uma resposta à necessidade de uma análise mais aprofundada e visual das oportunidades em múltiplas cidades. O `relatorio_comparativo_multicitadino.py` gera métricas chave como "Nº de cidades analisadas", "Média do score", "Desvio padrão" e "Replicabilidade (%)" por nicho, permitindo uma visão comparativa robusta. O `visualizar_comparativo_citadino.py` complementa isso, transformando esses dados em gráficos e tabelas coloridas, facilitando a identificação de nichos promissores e a compreensão da consistência e replicabilidade das oportunidades.

---

## 🧱 Etapas Principais (Fluxo Atual)

### 1. Coleta de Dados (google_maps_scraper.py)
- Utiliza o `google_maps_scraper.py` no modo "expansão" para coletar dados de empresas em diversas cidades e nichos, alimentando o banco de dados de oportunidades.

### 2. Análise e Consolidação (analisador_oportunidades.py)
- O `analisador_oportunidades.py` processa os dados brutos, calcula o "Score de Oportunidade" e consolida as informações no `oportunidades.db.csv`, gerenciando duplicatas e mantendo os registros mais recentes.

### 3. Geração de Relatório Comparativo (relatorio_comparativo_multicitadino.py)
- O `relatorio_comparativo_multicitadino.py` lê o `oportunidades.db.csv` e gera um relatório comparativo detalhado por nicho, incluindo métricas de consistência e replicabilidade, salvando-o em `data/relatorio_comparativo_multicitadino.csv`.

### 4. Visualização de Dados (visualizar_comparativo_citadino.py)
- O `visualizar_comparativo_citadino.py` cria visualizações gráficas (scatter plots, bar charts, heatmaps) e tabelas coloridas a partir do relatório comparativo, salvando-as em `data/imagens/`, para facilitar a interpretação e tomada de decisão.

---

## ⚙️ Stack Técnica
- **Python**: Linguagem de programação principal.
- **Pandas**: Manipulação e análise de dados.
- **Matplotlib**: Geração de gráficos e visualizações.
- **google-search-results (SerpApi)**: Para scraping de dados do Google Maps.
- **python-dotenv**: Gerenciamento de variáveis de ambiente.

---

## 📈 Indicadores de Sucesso
- Nichos validados/mês.
- Leads gerados/mês.
- Receita mensal de leads.
- Custo operacional (VPS, APIs).
- Tempo médio até rentabilidade (meta: < 90 dias por cidade).

---

## 📚 Próximos Passos
1. Criar planilha de hipóteses (Cidades × Nichos).
2. Montar o primeiro fluxo no n8n:
 - Input CSV → Scraper → Análise Sentimento → Ranking.
3. Testar 3 nichos em Itajubá e 3 no Rio.
4. Gerar relatório automatizado (PDF/Sheets).
5. Escolher 1 nicho vencedor e montar MVP de mídia (site/newsletter).

---

## 🧩 Extensões Futuras
- Dashboards com Streamlit ou Retool.
- API própria de validação de nichos.
- Marketplace local com IA integrada.
- Integração com CRM de parceiros.

---

## 🗝️ Filosofia do Projeto
> "Não concorra onde todos estão.  
>  Use IA para descobrir o que ninguém está olhando."

---

## 👥 Equipe e Funções
- **Ken** — fundador e estrategista.
- **Parceiros locais** — validadores e prestadores de serviço.

---

### pipeline
cidades.csv - nichos.csv
python google_maps_scraper.py
python analisador_oportunidades.py
python relatorio_oportunidades.py
python indexador_oportunidades.py

python consolidar.py

python google_maps_scraper.py --mode expansao
python relatorio_comparativo_multicitadino.py
python visualizar_comparativo_citadino.py

python filtrar_nichos_campeoes.py