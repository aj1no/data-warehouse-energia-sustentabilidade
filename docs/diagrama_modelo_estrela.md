# Diagrama do Modelo Estrela

**Autores:** Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar  
**Projeto:** Data Warehouse de Energia e Sustentabilidade  
**Data de entrega:** 03/06/2026

```mermaid
erDiagram
    "dw.dim_date" ||--o{ "dw.fact_energy_generation" : "date_key"
    "dw.dim_country" ||--o{ "dw.fact_energy_generation" : "country_key"
    "dw.dim_energy_source" ||--o{ "dw.fact_energy_generation" : "source_key"

    "dw.dim_date" {
        INTEGER date_key PK
        INTEGER year
        INTEGER decade
        DATE year_start_date
    }

    "dw.dim_country" {
        BIGINT country_key PK
        VARCHAR country_name
        VARCHAR iso_code
        VARCHAR population_band
        VARCHAR gdp_per_capita_band
        INTEGER start_year
        INTEGER end_year
        BOOLEAN is_current
    }

    "dw.dim_energy_source" {
        INTEGER source_key PK
        VARCHAR source_code
        VARCHAR source_name
        VARCHAR source_group
        BOOLEAN is_renewable
        BOOLEAN is_low_carbon
    }

    "dw.fact_energy_generation" {
        INTEGER date_key FK
        BIGINT country_key FK
        INTEGER source_key FK
        DOUBLE electricity_twh
        DOUBLE electricity_share_pct
        DOUBLE population
        DOUBLE gdp
        TIMESTAMP created_at
    }
```

## Grão da Tabela Fato

`dw.fact_energy_generation` possui uma linha por:

- país;
- ano;
- fonte de energia.

## Observação Sobre SCD Type 2

A dimensão `dw.dim_country` cria novas versões históricas quando há alteração em:

- `population_band`;
- `gdp_per_capita_band`.

A fato se conecta à versão válida para o ano da observação usando a condição:

```sql
o.year BETWEEN c.start_year AND c.end_year
```

