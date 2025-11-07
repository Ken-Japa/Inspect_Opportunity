![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=matplotlib&logoColor=white)
![SerpApi](https://img.shields.io/badge/SerpApi-000000?style=for-the-badge&logo=google&logoColor=white)
![python-dotenv](https://img.shields.io/badge/python--dotenv-F7DF1E?style=for-the-badge&logo=python&logoColor=black)

# Projeto Oportunidade de Negócio Brasil Maps 🧠🇧🇷

Automação e IA para encontrar, validar e monetizar negócios locais de alta margem.

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

# 🚀 Validador de Nicho — Manual Operacional

## 1️⃣ Objetivo

Validar de forma **enxuta e automatizada** se um nicho de serviço local tem demanda real e possibilidade de monetização via geração de leads ou operação direta.

---

## 2️⃣ Contexto de Aplicação

Usado **após a análise quantitativa e qualitativa**, quando:

- O nicho tem **score > 0.70** e **replicabilidade ≥ 70%**.
- Já existe clareza do público-alvo e do ticket médio.
- Deseja-se medir **interesse comercial real** via landing page e captação de leads.

---

## 3️⃣ Modelo Estratégico de Validação

### Etapa 1 — Criação da Landing Page

**Objetivo:** captar intenções de contato (leads) de potenciais clientes.

**Estrutura mínima da landing:**
| Seção | Elemento | Exemplo (para “Regularização de Galpões”) |
|--------|-----------|-------------------------------------------|
| Título | Problema + solução direta | “Regularize seu galpão industrial sem dor de cabeça — Diagnóstico gratuito em 24h.” |
| Benefícios | 3 bullets curtos | ✅ Evite multas e embargos <br> ✅ Regularize com engenheiro credenciado <br> ✅ Atendimento rápido e online |
| CTA | Formulário simples | Nome, cidade, WhatsApp, botão “Solicitar diagnóstico gratuito” |
| Prova social (opcional) | Logos ou selos | CREA, prefeitura, Procel, etc. |
| Rodapé | Cidade/região alvo | “Atendimento inicial em Itajubá e região” |

**Ferramentas sugeridas:**

- **Grátis / Low-cost:** [Carrd](https://carrd.co), [Framer](https://framer.com), [Webflow](https://webflow.com)
- **Formulário:** Google Forms, Tally, ou formulário nativo + Webhook.

---

### Etapa 2 — Fluxo de Captação e Gestão de Leads

**Pipeline básico:**
[Landing Page]
↓ Webhook / Form Response
[Google Sheets / Airtable]
↓
[n8n / Make → WhatsApp API]
↓
[Lead Qualificado]

yaml
Copy code

**Automação sugerida:**

1. Recebe formulário (nome, cidade, telefone).
2. Armazena no Google Sheets com timestamp.
3. Envia mensagem automática no WhatsApp:
   > “Olá {{nome}}, recebemos seu pedido de regularização. Em breve um engenheiro parceiro entrará em contato.”
4. Registra status do lead (`novo`, `contatado`, `convertido`).

---

### Etapa 3 — Modelo de Monetização (fase inicial)

#### 🔹 Opção A — Geração de Leads

- Venda direta para profissionais locais.
- Preço por lead: R$ 50–200 (depende do ticket do serviço).
- Cobrança inicial manual (Pix / planilha).

**Checklist:**

- [ ] Cadastrar 2–3 prestadores por nicho (engenheiros, despachantes, consultores).
- [ ] Criar grupo de WhatsApp “Parceiros — Regularização MG”.
- [ ] Enviar leads manualmente no início.
- [ ] Registrar feedback (fechou? preço? dificuldade?).

#### 🔹 Opção B — Intermediação Light

- Você faz o primeiro contato com o cliente (via WhatsApp Business).
- Fecha o contrato, repassa execução ao parceiro.
- Margem: 10–30%.

---

### Etapa 4 — Validação de Tração

**Período de teste:** 7–10 dias de tráfego leve (Google Ads ou orgânico).

**Indicadores de sucesso:**
| Indicador | Meta mínima |
|------------|--------------|
| Cliques na landing | 100+ |
| Leads (formulários) | ≥ 10 |
| Conversas iniciadas | ≥ 3 |
| Leads qualificados (reais) | ≥ 1 |
| Custo por lead (CPL) | ≤ R$ 20–40 |

**Se atingir 1 lead real**, o nicho é considerado validado.

---

### Etapa 5 — Conexão com Prestadores (Parcerias)

1. Procurar engenheiros, arquitetos e consultores locais (Google Maps, LinkedIn, CREA).
2. Criar planilha com:
   - Nome / WhatsApp
   - Cidade / área de atuação
   - Tipo de serviço
   - Disponibilidade / feedback
3. Estabelecer acordo simples (sem contrato formal no início):
   > “Te envio leads de clientes interessados, você paga comissão de X% sobre fechamento.”

---

## 4️⃣ Próximos Passos Após Validação

| Situação                               | Próxima Ação                             |
| -------------------------------------- | ---------------------------------------- |
| Nicho validado com 1+ lead real        | Criar rotina automatizada (n8n / Make)   |
| Prestadores ativos e feedback positivo | Formalizar comissão e criar mini CRM     |
| Nicho com alta tração                  | Iniciar operação direta (modelo híbrido) |
| Nicho sem conversão após 10 dias       | Reavaliar copy da landing e região-alvo  |

---

## 5️⃣ Escalabilidade

Após validar nicho:

- Replicar o mesmo processo para os outros.
- Automatizar fluxo de criação de landing + leads (template + IA).
- Criar painel central (`oportunidades_dashboard.csv` ou Notion) com:
  - Nicho
  - Score médio
  - Cidades testadas
  - CPL médio
  - Feedback dos prestadores

---

## 6️⃣ Próximas automações previstas

| Área           | Automação futura                                     | Benefício                                   |
| -------------- | ---------------------------------------------------- | ------------------------------------------- |
| Scraper        | Simulação humana para contornar rate limits          | Libera coleta contínua                      |
| Score dinâmico | Integração com Google Trends, Preços, Concorrência   | Detecta novas oportunidades automaticamente |
| Leads          | Classificação automática via IA (Lead quente / frio) | Economia de tempo                           |
| Operação       | Geração automática de contrato / proposta            | Escala comercial real                       |

---

## 7️⃣ Síntese Estratégica

- Comece como **gerador de leads inteligente** (baixo risco, alta informação).
- Use a fase de repasse para **formar rede de parceiros e entender o serviço.**
- Quando o fluxo e ticket estiverem previsíveis, **migre para operador híbrido.**
- A automação e IA virão como **multiplicadores de escala**, não como ponto de partida.

---

📁 Estrutura recomendada de pastas:
/validacao_nicho/
│
├── landing_pages/
│ ├── regularizacao_galpoes.html
│ └── acessibilidade_publica.html
│
├── leads/
│ └── leads_registro.csv
│
├── parceiros/
│ └── engenheiros_mg.csv
│
└── relatorios/
├── validacao_galpoes.md
└── validacao_outorga.md
