# Data Warehouse de Energia e Sustentabilidade com DuckDB

**Instituição**: Faculdade de Tecnologia de Jundiaí (FATEC Jundiaí)
**Disciplina**: Banco e Armazém de Dados em Ciências de Dados
**Professor**: Rafael Gross
**Autores**:
* Rodolfo Vinicius Cima Takemoto
* Tiago Galhardo Avelar

---

## 1. Descrição do Problema

A transição energética mundial exige o acompanhamento histórico da geração elétrica por diferentes fontes de energia. Entretanto, datasets públicos sobre energia costumam estar em formato amplo, com muitas colunas por fonte, o que dificulta análises comparativas, consultas históricas e construção de indicadores por país, ano e tipo de fonte.

Este projeto organiza esses dados em um **Data Warehouse dimensional**, permitindo analisar a evolução da geração elétrica renovável, fóssil e de baixo carbono entre países e ao longo do tempo.

---

## 2. Descrição do Dataset

O projeto utiliza o **Our World in Data Energy Dataset**, base pública mantida pela Our World in Data.

* **Arquivo base**: `data/raw/owid-energy-data.csv`
* **Fonte pública**: `https://owid-public.owid.io/data/energy/owid-energy-data.csv`
* **Conteúdo**: dados anuais por país, incluindo população, PIB e geração elétrica por fonte, como solar, eólica, hidrelétrica, carvão, gás, óleo, nuclear, biocombustíveis e outras renováveis.

---

## 3. Objetivo

O objetivo geral é construir um Data Warehouse completo em **DuckDB**, com pipeline SQL e Python, para analisar a evolução da geração elétrica por fonte de energia.

O grão da tabela fato principal é:

> Uma linha por país, ano e fonte de energia.

---

## 4. Metodologia

O desenvolvimento do projeto seguiu as etapas abaixo:

1. **Ingestão dos dados brutos**: leitura do CSV original para a camada de staging.
2. **Normalização intermediária**: transformação da base ampla em estrutura longa na camada OLTP.
3. **Modelagem dimensional**: criação de dimensões e tabela fato em modelo estrela.
4. **Carga do Data Warehouse**: execução de pipeline SQL idempotente em DuckDB.
5. **Historização de país**: implementação de SCD Type 2 na dimensão `dw.dim_country`.
6. **Consultas analíticas**: criação de consultas para análise temporal, ranking, agregação multidimensional, cohort e KPI.
7. **Validações**: checagem de contagens, chaves estrangeiras, integridade e totais por fonte.
8. **Visualizações**: geração de gráficos, dashboard HTML e relatório técnico em PDF.

---

## 5. Modelagem Dimensional

O Data Warehouse utiliza um modelo estrela com três dimensões principais e uma tabela fato central.

| Objeto | Descrição |
| :--- | :--- |
| `dw.dim_date` | Dimensão de tempo, com ano, década e indicadores de ano atual e ano mais recente do dataset. |
| `dw.dim_country` | Dimensão de país com SCD Type 2, controlando mudanças de faixa populacional e PIB per capita. |
| `dw.dim_energy_source` | Dimensão de fonte energética, classificando as fontes em renováveis, fósseis e baixo carbono. |
| `dw.fact_energy_generation` | Tabela fato com geração elétrica em TWh, participação percentual, população e PIB. |
| `dw.fact_energy_generation_annual_grouped` | Tabela agregada para comparação de performance. |

---

## 6. Consultas Analíticas

O projeto entrega cinco consultas analíticas principais:

1. **Evolução temporal** da geração solar, eólica e hidrelétrica no Brasil.
2. **Ranking Top 10** de países com maior geração renovável no ano mais recente.
3. **Agregação multidimensional** por país, ano e grupo de fonte.
4. **Cohort/retenção** de países que ultrapassaram 1% de geração solar.
5. **KPI de negócio** com percentual de geração renovável sobre o total modelado.

---

## 7. Resultados e Entregáveis

Os principais artefatos gerados pelo projeto estão organizados da seguinte forma:

| Caminho | Conteúdo |
| :--- | :--- |
| `database/energy_dw.duckdb` | Banco DuckDB com o Data Warehouse. |
| `docs/relatorio_tecnico.pdf` | Relatório técnico acadêmico em PDF. |
| `docs/relatorio_tecnico.md` | Relatório técnico em Markdown. |
| `docs/dicionario_dados.md` | Dicionário de dados. |
| `docs/diagrama_modelo_estrela.md` | Documentação do modelo estrela. |
| `docs/diagrama_modelo_estrela.png` | Diagrama visual do modelo estrela. |
| `docs/roteiro_apresentacao.md` | Roteiro de apresentação. |
| `outputs/dashboard.html` | Dashboard HTML. |
| `outputs/figures/` | Gráficos gerados. |
| `outputs/queries/` | Consultas analíticas e validações exportadas. |

---

## 8. Execução

```bash
pip install -r requirements.txt
python run_all.py
```

Ao final da execução, o pipeline gera o banco DuckDB, exporta as consultas, cria os gráficos e abre automaticamente o dashboard HTML no navegador padrão.

---

## 9. Checklist Acadêmico

* [x] Uso do DuckDB como banco principal.
* [x] Camada de staging.
* [x] Camada OLTP intermediária.
* [x] Modelo dimensional em estrela.
* [x] Dimensão de data.
* [x] Dimensão de país com SCD Type 2.
* [x] Dimensão de fonte de energia.
* [x] Tabela fato com grão definido.
* [x] Chaves substitutas nas dimensões.
* [x] Pipeline SQL idempotente.
* [x] Validações de qualidade e integridade.
* [x] Cinco consultas analíticas.
* [x] Visualizações e dashboard HTML.
* [x] Tabela agregada para análise de performance.
* [x] Relatório técnico em PDF.
* [x] Banco `.duckdb` incluído para entrega via GitHub.
