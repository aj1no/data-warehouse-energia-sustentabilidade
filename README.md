# Data Warehouse de Energia e Sustentabilidade

**Autores:** Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar  
**Professor:** Rafael Gross  
**Disciplina:** Banco e Armazém de Dados em Ciências de Dados  


## Objetivo do Projeto

Construir um Data Warehouse em DuckDB para analisar a evolução da geração elétrica por fonte de energia, comparando fontes renováveis, fósseis e de baixo carbono entre países e ao longo do tempo.

O grão da tabela fato `dw.fact_energy_generation` é: **uma linha por país, ano e fonte de energia**.

## Dataset Utilizado

O projeto utiliza o **Our World in Data Energy Dataset**, disponibilizado publicamente pela Our World in Data.

- Arquivo original: `data/raw/owid-energy-data.csv`
- Fonte: `https://owid-public.owid.io/data/energy/owid-energy-data.csv`

## Estrutura do Projeto

```text
.
├── data/raw/                         # Dataset original
├── database/                         # Banco DuckDB gerado
├── docs/                             # Documentação acadêmica e técnica
├── outputs/                          # Consultas, gráficos e dashboard
├── scripts/                          # Pipeline SQL e geração de artefatos
├── dashboard.html                    # Cópia principal do dashboard
├── requirements.txt                  # Dependências Python
└── run_all.py                        # Execução completa do projeto
```

## Execução

```bash
pip install -r requirements.txt
python run_all.py
```

## Principais Entregáveis

- `database/energy_dw.duckdb`: banco de dados DuckDB com o Data Warehouse.
- `docs/relatorio_tecnico.pdf`: relatório técnico acadêmico em PDF.
- `docs/relatorio_tecnico.md`: versão Markdown do relatório técnico.
- `docs/dicionario_dados.md`: dicionário de dados.
- `docs/diagrama_modelo_estrela.md`: documentação do modelo estrela.
- `docs/diagrama_modelo_estrela.png`: diagrama visual do modelo estrela.
- `docs/roteiro_apresentacao.md`: roteiro de apresentação do projeto.
- `outputs/dashboard.html`: dashboard HTML.
- `outputs/figures/`: gráficos gerados.
- `outputs/queries/`: consultas analíticas e validações exportadas.
- `scripts/`: scripts SQL do pipeline e script de geração de artefatos.

## Checklist Acadêmico

- [x] Uso do DuckDB como banco principal.
- [x] Camada de staging.
- [x] Camada OLTP intermediária.
- [x] Modelo dimensional em estrela.
- [x] Dimensão de data: `dw.dim_date`.
- [x] Dimensão de país com SCD Type 2: `dw.dim_country`.
- [x] Dimensão de fonte de energia: `dw.dim_energy_source`.
- [x] Tabela fato: `dw.fact_energy_generation`.
- [x] Chaves substitutas nas dimensões.
- [x] Grão da fato definido como país, ano e fonte de energia.
- [x] Pipeline SQL idempotente.
- [x] Validações de qualidade e integridade.
- [x] Cinco consultas analíticas obrigatórias.
- [x] Visualizações e dashboard HTML.
- [x] Tabela agregada para análise de performance.
- [x] Relatório técnico em PDF.
- [x] Banco `.duckdb` incluído para entrega via GitHub.
