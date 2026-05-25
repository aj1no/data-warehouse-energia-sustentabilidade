# Relatório Técnico

**Autores:** Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar  
**Projeto:** Data Warehouse de Energia e Sustentabilidade  
**Disciplina:** Banco e Armazém de Dados em Ciências de Dados  
**Data de entrega:** 03/06/2026

## 1. Resumo Executivo

Este projeto constrói um Data Warehouse em DuckDB para analisar a geração elétrica mundial por fonte de energia. O foco analítico é comparar fontes renováveis, fósseis e de baixo carbono entre países e ao longo do tempo, com ênfase em consultas de evolução temporal, ranking, agregação multidimensional, cohort e KPI.

O pipeline foi projetado para rodar do zero: baixa o dataset real da Our World in Data, cria as camadas staging, OLTP intermediária e dimensional, executa validações, exporta consultas e gera visualizações.

## 2. Introdução

A transição energética exige monitoramento histórico da participação de fontes renováveis, fósseis e de baixo carbono na matriz elétrica. Um Data Warehouse facilita esse acompanhamento porque organiza os dados em um modelo dimensional, melhora a legibilidade das consultas analíticas e permite criar agregações para desempenho.

## 3. Fonte de Dados

A fonte utilizada é o **Our World in Data Energy Dataset**, disponível em:

<https://owid-public.owid.io/data/energy/owid-energy-data.csv>

O dataset contém observações por país e ano, incluindo população, PIB e métricas de energia. Para este projeto foram usadas colunas de geração elétrica por fonte, como solar, eólica, hidrelétrica, carvão, gás, óleo, nuclear, biocombustível e outras renováveis.

## 4. Modelagem Dimensional

O modelo dimensional segue o padrão estrela. A tabela fato `dw.fact_energy_generation` possui o grão de uma linha por país, ano e fonte de energia.

Dimensões:

- `dw.dim_date`: representa o ano da observação.
- `dw.dim_country`: representa países com histórico SCD Type 2.
- `dw.dim_energy_source`: classifica fontes em `Renewable`, `Fossil` e `Low Carbon`.

Tabela fato:

- `dw.fact_energy_generation`: armazena geração elétrica em TWh, participação percentual, população, PIB e timestamp de carga.

## 5. Pipeline ETL

O pipeline é dividido em seis scripts SQL:

1. `00_staging.sql`: lê o CSV original e cria a staging padronizada.
2. `01_oltp.sql`: cria tabelas intermediárias normalizadas.
3. `02_dw_model.sql`: define a estrutura do Data Warehouse.
4. `03_etl_load.sql`: carrega dimensões e fato, incluindo SCD Type 2.
5. `04_analytics.sql`: cria consultas analíticas e validações.
6. `05_performance.sql`: cria tabela agregada e consultas de referência para benchmark.

O script `run_all.py` orquestra todas as etapas e garante que o dataset seja baixado apenas quando ainda não existir localmente.

## 6. Consultas Analíticas

Foram implementadas cinco consultas obrigatórias:

- **Q1 - Evolução temporal:** evolução da geração solar, eólica e hidrelétrica no Brasil por ano.
- **Q2 - Ranking TOP N:** Top 10 países com maior geração renovável no ano mais recente disponível.
- **Q3 - Agregação multidimensional:** geração elétrica por grupo de fonte e país no ano mais recente.
- **Q4 - Cohort/retenção:** países que ultrapassaram 1% de geração solar pela primeira vez e retenção acima do patamar nos anos seguintes.
- **Q5 - KPI:** percentual de geração renovável sobre a geração total modelada por país e ano.

As saídas são exportadas para `outputs/queries`.

## 7. Visualizações

O projeto gera quatro visualizações:

- gráfico de linha da evolução de solar, eólica e hidrelétrica no Brasil;
- gráfico de barras com os 10 países de maior geração renovável no ano mais recente;
- heatmap de participação das fontes na matriz elétrica brasileira;
- dashboard HTML com KPIs, gráficos e tabela de performance.

Os arquivos são salvos em `outputs/figures` e `outputs/dashboard.html`.

## 8. Performance

Foi criada a tabela agregada `dw.fact_energy_generation_annual_grouped`, com agregação por ano, país e grupo de fonte.

A comparação de performance é feita pelo `run_all.py`, que executa repetidamente:

- uma consulta sobre a fato original com joins nas dimensões;
- uma consulta equivalente sobre a tabela agregada.

Os tempos medidos são salvos em:

- `outputs/queries/analytics_performance_benchmark.csv`
- `outputs/performance_summary.md`

Na execução validada do projeto, com o dataset real baixado em `data/raw/owid-energy-data.csv`, foram realizadas 7 execuções por consulta. A consulta sobre a fato original retornou 261 linhas, com melhor tempo de 8,648 ms e média de 9,302 ms. A consulta sobre a tabela agregada retornou as mesmas 261 linhas, com melhor tempo de 2,722 ms e média de 3,034 ms.

O ganho médio observado foi de **3,07x** ao usar `dw.fact_energy_generation_annual_grouped`. Os valores também estão registrados em `outputs/performance_summary.md`.

## 9. Desafios e Soluções

Um desafio central foi transformar o dataset original, que possui colunas largas por fonte de energia, em uma estrutura longa compatível com uma tabela fato dimensional. A solução foi criar `oltp.energy_source_observations`, que normaliza as fontes em linhas.

Outro ponto foi implementar histórico de países. A dimensão `dw.dim_country` usa SCD Type 2 e cria novas versões quando mudam as faixas de população ou de PIB per capita, preservando a versão correta para cada ano da fato.

Também foram criadas validações para contagem de linhas, chaves estrangeiras nulas, integridade referencial e totais de geração por fonte.

## 10. Conclusão

O projeto entrega um Data Warehouse completo, reexecutável e documentado, usando DuckDB, SQL e Python. O modelo estrela facilita análises temporais e comparações entre países e fontes de energia, enquanto as validações e a tabela agregada reforçam qualidade e desempenho.

## 11. Referências

- Our World in Data. Energy Dataset. <https://owid-public.owid.io/data/energy/owid-energy-data.csv>
- Our World in Data. Energy Data Repository. <https://github.com/owid/energy-data>
- DuckDB Documentation. <https://duckdb.org/docs/>
