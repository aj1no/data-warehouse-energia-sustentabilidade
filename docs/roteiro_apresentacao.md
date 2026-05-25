# Roteiro de Apresentação

**Autores:** Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar  
**Projeto:** Data Warehouse de Energia e Sustentabilidade  
**Duração estimada:** 10 a 15 minutos  
**Data de entrega:** 03/06/2026

## 1. Abertura e Problema de Negócio (1 minuto)

Apresentar o objetivo do projeto: construir um Data Warehouse para analisar a evolução da geração elétrica por fonte de energia. Explicar que a motivação é comparar fontes renováveis, fósseis e de baixo carbono entre países e ao longo do tempo.

## 2. Dataset Utilizado (1 minuto)

Explicar que a fonte é o **Our World in Data Energy Dataset**, baixado automaticamente pelo `run_all.py` a partir do CSV público. Comentar que o dataset contém dados por país e ano, incluindo geração elétrica por fonte, população e PIB.

## 3. Modelagem Dimensional (2 minutos)

Mostrar o modelo estrela em `docs/diagrama_modelo_estrela.md` e `docs/diagrama_modelo_estrela.png`. Explicar que o grão da tabela fato é uma linha por país, ano e fonte de energia.

## 4. Tabela Fato (1 minuto)

Apresentar `dw.fact_energy_generation`:

- `date_key`
- `country_key`
- `source_key`
- `electricity_twh`
- `electricity_share_pct`
- `population`
- `gdp`
- `created_at`

Destacar que a tabela fato permite comparar evolução temporal, países e fontes energéticas.

## 5. Dimensões (2 minutos)

Apresentar as dimensões:

- `dw.dim_date`: ano, década e data inicial do ano.
- `dw.dim_country`: país, ISO, faixas de população e PIB per capita.
- `dw.dim_energy_source`: fontes e classificação em `Renewable`, `Fossil` e `Low Carbon`.

Explicar que `dw.dim_energy_source` classifica solar, eólica, hidrelétrica, biocombustível e outras renováveis como `Renewable`; carvão, gás e óleo como `Fossil`; nuclear como `Low Carbon`.

## 6. SCD Type 2 (1 minuto)

Explicar que `dw.dim_country` implementa SCD Type 2. Uma nova versão do país é criada quando muda:

- a faixa populacional;
- a faixa de PIB per capita.

Mostrar que a fato se liga à versão correta usando o intervalo `start_year` e `end_year`.

## 7. Pipeline ETL (2 minutos)

Explicar a ordem dos scripts:

1. `00_staging.sql`: leitura do CSV.
2. `01_oltp.sql`: normalização intermediária.
3. `02_dw_model.sql`: criação do modelo dimensional.
4. `03_etl_load.sql`: carga das dimensões e fato.
5. `04_analytics.sql`: consultas e validações.
6. `05_performance.sql`: tabela agregada e comparação de performance.

Destacar que o pipeline é idempotente e pode ser executado várias vezes sem duplicar dados.

## 8. Consultas Analíticas (1 a 2 minutos)

Apresentar as cinco consultas:

- Q1: evolução solar, eólica e hidrelétrica no Brasil.
- Q2: Top 10 países por geração renovável no ano mais recente.
- Q3: geração por grupo de fonte e país.
- Q4: cohort de países que ultrapassaram 1% de geração solar.
- Q5: KPI de percentual renovável por país e ano.

## 9. Gráficos e Dashboard (1 a 2 minutos)

Mostrar:

- gráfico de linha em `outputs/figures/brazil_renewable_evolution.svg`;
- gráfico de barras em `outputs/figures/top10_renewable_latest_year.svg`;
- heatmap em `outputs/figures/brazil_source_share_heatmap.svg`;
- dashboard em `outputs/dashboard.html` e `dashboard.html`.

Explicar que o dashboard reúne KPIs, gráficos e tabela de performance.

## 10. Validações (1 minuto)

Mostrar que foram criadas validações para:

- contagem de linhas;
- chaves estrangeiras nulas;
- integridade entre fato e dimensões;
- total de geração elétrica por fonte;
- duplicidade no grão da fato.

## 11. Performance (1 minuto)

Explicar a tabela agregada `dw.fact_energy_generation_annual_grouped`, criada por ano, país e grupo de fonte. Apresentar a comparação entre consulta na fato original e consulta na tabela agregada, com os resultados salvos em `outputs/performance_summary.md`.

## 12. Conclusão (1 minuto)

Concluir que o projeto entrega um Data Warehouse completo, com modelo estrela, SCD Type 2, pipeline idempotente, consultas analíticas, validações, visualizações, dashboard, relatório técnico em PDF e banco DuckDB versionado para entrega pelo GitHub.

