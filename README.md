# Data Warehouse de Energia e Sustentabilidade

**Autores:** Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar  
**Disciplina:** Banco e Armazém de Dados em Ciências de Dados  
**Data de entrega:** 03/06/2026  
**Dataset:** Our World in Data Energy Dataset

## Objetivo

Construir um Data Warehouse completo em DuckDB para analisar a evolução da geração elétrica por fonte de energia, comparando fontes renováveis, fósseis e de baixo carbono entre países e ao longo do tempo.

O grão da tabela fato é: **uma linha por país, ano e fonte de energia**.

## Entrega pelo GitHub

Este repositório contém todos os arquivos necessários para a entrega final pelo GitHub, incluindo código, documentação, relatório em PDF, banco DuckDB, CSV original, consultas exportadas, gráficos e dashboard.

Link do repositório:

```text
https://github.com/aj1no/data-warehouse-energia-sustentabilidade
```

Arquivos principais da entrega:

- Relatório técnico em PDF: `docs/relatorio_tecnico.pdf`
- Relatório técnico em Markdown: `docs/relatorio_tecnico.md`
- Dashboard HTML: `outputs/dashboard.html` e `dashboard.html`
- Gráficos: `outputs/figures/`
- Banco DuckDB: `database/energy_dw.duckdb`
- Dataset CSV original: `data/raw/owid-energy-data.csv`
- Consultas exportadas: `outputs/queries/`
- Dicionário de dados: `docs/dicionario_dados.md`
- Diagrama do modelo estrela: `docs/diagrama_modelo_estrela.md` e `docs/diagrama_modelo_estrela.png`
- Roteiro de apresentação: `docs/roteiro_apresentacao.md`

Para instalar dependências:

```powershell
pip install -r requirements.txt
```

Para executar o projeto:

```powershell
python run_all.py
```

No Windows/VSCode, caso o Python não esteja no PATH, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_project.ps1
```

## Como Instalar Dependências

Crie um ambiente virtual e instale as bibliotecas:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Dependências principais:

- `duckdb`: banco analítico principal.
- `pandas`: exportação e apoio à geração de visualizações.

## Como Executar

Execute o pipeline completo:

```powershell
python run_all.py
```

No Windows/VSCode, se aparecer erro de `python` não encontrado ou bloqueio de execução de scripts, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_project.ps1
```

Esse script instala as dependências necessárias e executa o projeto.

Evite executar com Python 3.14 global do VSCode. Este projeto foi validado com Python 3.12; a pasta `.vscode` já aponta para `.venv\Scripts\python.exe`. Se o VSCode insistir em outro interpretador, use `Ctrl+Shift+P` > `Python: Select Interpreter` > `Enter interpreter path` e selecione:

```text
.\.venv\Scripts\python.exe
```

O script:

- baixa `owid-energy-data.csv` se ele ainda não existir;
- cria o banco DuckDB em `database/energy_dw.duckdb`;
- executa os scripts SQL na ordem exigida;
- exporta consultas e validações para `outputs/queries`;
- gera gráficos SVG em `outputs/figures`;
- gera o dashboard em `outputs/dashboard.html` e também em `dashboard.html`.

## Como Abrir o Banco DuckDB

Pelo Python:

```python
import duckdb
conn = duckdb.connect("database/energy_dw.duckdb")
conn.sql("SELECT * FROM dw.fact_energy_generation LIMIT 10").show()
```

Ou pela CLI do DuckDB, se instalada:

```powershell
duckdb database/energy_dw.duckdb
```

## Estrutura das Pastas

```text
.
├── data/
│   └── raw/
│       └── owid-energy-data.csv
├── database/
│   └── energy_dw.duckdb
├── docs/
│   ├── dicionario_dados.md
│   ├── diagrama_modelo_estrela.md
│   ├── diagrama_modelo_estrela.png
│   ├── relatorio_tecnico.md
│   ├── relatorio_tecnico.pdf
│   └── roteiro_apresentacao.md
├── outputs/
│   ├── dashboard.html
│   ├── figures/
│   └── queries/
├── scripts/
│   ├── 00_staging.sql
│   ├── 01_oltp.sql
│   ├── 02_dw_model.sql
│   ├── 03_etl_load.sql
│   ├── 04_analytics.sql
│   └── 05_performance.sql
├── dashboard.html
├── requirements.txt
├── run_project.ps1
└── run_all.py
```

## Scripts SQL

1. `scripts/00_staging.sql`: lê o CSV original e padroniza colunas relevantes.
2. `scripts/01_oltp.sql`: cria tabelas intermediárias normalizadas.
3. `scripts/02_dw_model.sql`: define dimensões e fato no modelo estrela.
4. `scripts/03_etl_load.sql`: carrega dimensões, SCD Type 2 e fato.
5. `scripts/04_analytics.sql`: cria consultas analíticas e validações.
6. `scripts/05_performance.sql`: cria tabela agregada e consultas de comparação.

## Consultas Analíticas Entregues

- Q1: evolução da geração solar, eólica e hidrelétrica no Brasil por ano.
- Q2: Top 10 países com maior geração renovável no ano mais recente disponível.
- Q3: geração elétrica por grupo de fonte e país no ano mais recente.
- Q4: cohort de países que ultrapassaram 1% de geração solar pela primeira vez.
- Q5: KPI de percentual renovável sobre geração total modelada por país e ano.

## Visualizações

- Linha: `outputs/figures/brazil_renewable_evolution.svg`
- Barras: `outputs/figures/top10_renewable_latest_year.svg`
- Heatmap: `outputs/figures/brazil_source_share_heatmap.svg`
- Dashboard HTML: `outputs/dashboard.html` e `dashboard.html`

## Entregáveis

- Código SQL e Python do pipeline.
- Banco DuckDB gerado após execução.
- Dataset CSV original.
- Relatório técnico em PDF.
- Roteiro de apresentação.
- Consultas analíticas exportadas em CSV.
- Validações de qualidade de dados.
- Visualizações e dashboard HTML.
- Documentação técnica, dicionário de dados e diagrama do modelo estrela.

## Checklist de Avaliação

- [x] 3 dimensões ou mais.
- [x] 1 tabela fato.
- [x] Dimensão de data.
- [x] SCD Type 2.
- [x] Chaves substitutas.
- [x] Pipeline idempotente.
- [x] Validações.
- [x] 5 consultas analíticas.
- [x] 4 visualizações.
- [x] Tabela agregada de performance.
- [x] Relatório técnico em PDF.
- [x] Dashboard.
- [x] Banco `.duckdb`.
