# Dicionário de Dados

**Autores:** Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar  
**Projeto:** Data Warehouse de Energia e Sustentabilidade  
**Data de entrega:** 03/06/2026

## Camada Staging

### `stg.energy_raw`

Tabela criada diretamente a partir do CSV original `owid-energy-data.csv`, mantendo as colunas disponibilizadas pela Our World in Data.

### `stg.energy_standardized`

| Campo | Tipo | Descrição |
|---|---|---|
| `country_name` | VARCHAR | Nome do país ou entidade na origem. |
| `iso_code` | VARCHAR | Código ISO de três letras. Registros não nacionais são filtrados nas camadas seguintes. |
| `year` | INTEGER | Ano da observação. |
| `population` | DOUBLE | População estimada. |
| `gdp` | DOUBLE | PIB informado no dataset. |
| `*_electricity` | DOUBLE | Geração elétrica anual da fonte em TWh. |
| `*_share_elec` | DOUBLE | Participação percentual da fonte na eletricidade, quando disponível. |

## Camada OLTP Intermediária

### `oltp.country_year_metrics`

| Campo | Tipo | Descrição |
|---|---|---|
| `country_name` | VARCHAR | Nome do país. |
| `iso_code` | VARCHAR | Código ISO de três letras. |
| `year` | INTEGER | Ano da observação. |
| `population` | DOUBLE | População no ano. |
| `gdp` | DOUBLE | PIB no ano. |
| `population_band` | VARCHAR | Faixa populacional usada no SCD Type 2. |
| `gdp_per_capita_band` | VARCHAR | Faixa de PIB per capita usada no SCD Type 2. |
| `gdp_per_capita` | DOUBLE | PIB dividido pela população, quando possível. |

Faixas populacionais:

- `Unknown`
- `Até 1 milhão`
- `1 a 10 milhões`
- `10 a 100 milhões`
- `Acima de 100 milhões`

Faixas de PIB per capita:

- `Unknown`
- `Baixo`
- `Médio`
- `Alto`

### `oltp.energy_source_observations`

| Campo | Tipo | Descrição |
|---|---|---|
| `country_name` | VARCHAR | Nome do país. |
| `iso_code` | VARCHAR | Código ISO de três letras. |
| `year` | INTEGER | Ano da observação. |
| `source_code` | VARCHAR | Código padronizado da fonte. |
| `source_name` | VARCHAR | Nome da fonte energética. |
| `electricity_twh` | DOUBLE | Geração elétrica em TWh. |
| `electricity_share_pct` | DOUBLE | Participação percentual da fonte na matriz elétrica. |
| `population` | DOUBLE | População no ano. |
| `gdp` | DOUBLE | PIB no ano. |

## Modelo Dimensional

### `dw.dim_date`

| Campo | Tipo | Descrição |
|---|---|---|
| `date_key` | INTEGER | Chave substituta no formato `YYYY0101`. |
| `year` | INTEGER | Ano. |
| `decade` | INTEGER | Década do ano. |
| `year_start_date` | DATE | Primeiro dia do ano. |
| `is_current_year` | BOOLEAN | Indica se o ano corresponde ao ano atual do sistema. |
| `is_latest_dataset_year` | BOOLEAN | Indica se o ano corresponde ao ano mais recente disponível no dataset. |

### `dw.dim_country`

Dimensão com SCD Type 2. Uma nova versão é criada sempre que muda a faixa populacional ou a faixa de PIB per capita.

| Campo | Tipo | Descrição |
|---|---|---|
| `country_key` | BIGINT | Chave substituta da versão do país. |
| `country_name` | VARCHAR | Nome do país. |
| `iso_code` | VARCHAR | Código ISO de três letras. |
| `population_band` | VARCHAR | Faixa populacional vigente no intervalo. |
| `gdp_per_capita_band` | VARCHAR | Faixa de PIB per capita vigente no intervalo. |
| `start_year` | INTEGER | Primeiro ano da versão SCD. |
| `end_year` | INTEGER | Último ano da versão SCD. |
| `is_current` | BOOLEAN | Indica a versão mais recente do país. |

### `dw.dim_energy_source`

| Campo | Tipo | Descrição |
|---|---|---|
| `source_key` | INTEGER | Chave substituta da fonte. |
| `source_code` | VARCHAR | Código padronizado da fonte. |
| `source_name` | VARCHAR | Nome da fonte. |
| `source_group` | VARCHAR | Grupo: `Renewable`, `Fossil` ou `Low Carbon`. |
| `is_renewable` | BOOLEAN | Indica se a fonte é renovável. |
| `is_low_carbon` | BOOLEAN | Indica se a fonte é de baixo carbono. |

Classificação:

| Fonte | Grupo |
|---|---|
| Solar | Renewable |
| Wind | Renewable |
| Hydro | Renewable |
| Biofuel | Renewable |
| Other renewable | Renewable |
| Coal | Fossil |
| Gas | Fossil |
| Oil | Fossil |
| Nuclear | Low Carbon |

### `dw.fact_energy_generation`

Grão: **uma linha por país, ano e fonte de energia**.

| Campo | Tipo | Descrição |
|---|---|---|
| `date_key` | INTEGER | FK para `dw.dim_date`. |
| `country_key` | BIGINT | FK para `dw.dim_country`, respeitando a versão SCD do ano. |
| `source_key` | INTEGER | FK para `dw.dim_energy_source`. |
| `electricity_twh` | DOUBLE | Geração elétrica da fonte no ano em TWh. |
| `electricity_share_pct` | DOUBLE | Participação percentual da fonte, quando disponível. |
| `population` | DOUBLE | População do país no ano. |
| `gdp` | DOUBLE | PIB do país no ano. |
| `created_at` | TIMESTAMP | Momento de carga do registro. |

### `dw.fact_energy_generation_annual_grouped`

Tabela agregada de performance.

| Campo | Tipo | Descrição |
|---|---|---|
| `year` | INTEGER | Ano. |
| `country_name` | VARCHAR | País. |
| `source_group` | VARCHAR | Grupo da fonte. |
| `electricity_twh` | DOUBLE | Soma anual da geração elétrica em TWh. |

## Saídas Analíticas

As consultas e validações são materializadas no schema `analytics` e exportadas para `outputs/queries`.

