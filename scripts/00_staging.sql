-- Projeto: Data Warehouse de Energia e Sustentabilidade
-- Autores: Dalmir Doneda Júnior; Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar
-- Etapa 00: cria a camada staging a partir do CSV original da Our World in Data.

CREATE SCHEMA IF NOT EXISTS stg;

CREATE OR REPLACE TABLE stg.energy_raw AS
SELECT *
FROM read_csv_auto(
    '${RAW_CSV_PATH}',
    header = true,
    sample_size = -1,
    ignore_errors = true,
    union_by_name = true,
    nullstr = ['', 'NA', 'NaN', 'nan']
);

CREATE OR REPLACE TABLE stg.energy_standardized AS
SELECT
    country::VARCHAR AS country_name,
    iso_code::VARCHAR AS iso_code,
    TRY_CAST(year AS INTEGER) AS year,
    TRY_CAST(population AS DOUBLE) AS population,
    TRY_CAST(gdp AS DOUBLE) AS gdp,
    TRY_CAST(solar_electricity AS DOUBLE) AS solar_electricity,
    TRY_CAST(solar_share_elec AS DOUBLE) AS solar_share_elec,
    TRY_CAST(wind_electricity AS DOUBLE) AS wind_electricity,
    TRY_CAST(wind_share_elec AS DOUBLE) AS wind_share_elec,
    TRY_CAST(hydro_electricity AS DOUBLE) AS hydro_electricity,
    TRY_CAST(hydro_share_elec AS DOUBLE) AS hydro_share_elec,
    TRY_CAST(coal_electricity AS DOUBLE) AS coal_electricity,
    TRY_CAST(coal_share_elec AS DOUBLE) AS coal_share_elec,
    TRY_CAST(gas_electricity AS DOUBLE) AS gas_electricity,
    TRY_CAST(gas_share_elec AS DOUBLE) AS gas_share_elec,
    TRY_CAST(oil_electricity AS DOUBLE) AS oil_electricity,
    TRY_CAST(oil_share_elec AS DOUBLE) AS oil_share_elec,
    TRY_CAST(nuclear_electricity AS DOUBLE) AS nuclear_electricity,
    TRY_CAST(nuclear_share_elec AS DOUBLE) AS nuclear_share_elec,
    TRY_CAST(biofuel_electricity AS DOUBLE) AS biofuel_electricity,
    TRY_CAST(biofuel_share_elec AS DOUBLE) AS biofuel_share_elec,
    TRY_CAST(other_renewable_electricity AS DOUBLE) AS other_renewable_electricity,
    TRY_CAST(other_renewables_share_elec AS DOUBLE) AS other_renewables_share_elec
FROM stg.energy_raw
WHERE country IS NOT NULL
  AND TRY_CAST(year AS INTEGER) IS NOT NULL;

