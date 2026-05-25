-- Projeto: Data Warehouse de Energia e Sustentabilidade
-- Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar
-- Entrega: 03/06/2026
-- Etapa 01: cria uma camada OLTP normalizada/intermediária para simplificar o ETL dimensional.

CREATE SCHEMA IF NOT EXISTS oltp;

CREATE OR REPLACE TABLE oltp.country_year_metrics AS
SELECT DISTINCT
    country_name,
    iso_code,
    year,
    population,
    gdp,
    CASE
        WHEN population IS NULL OR population <= 0 THEN 'Unknown'
        WHEN population <= 1000000 THEN 'Até 1 milhão'
        WHEN population <= 10000000 THEN '1 a 10 milhões'
        WHEN population <= 100000000 THEN '10 a 100 milhões'
        ELSE 'Acima de 100 milhões'
    END AS population_band,
    CASE
        WHEN population IS NULL OR population <= 0 OR gdp IS NULL OR gdp <= 0 THEN 'Unknown'
        WHEN gdp / population < 5000 THEN 'Baixo'
        WHEN gdp / population < 20000 THEN 'Médio'
        ELSE 'Alto'
    END AS gdp_per_capita_band,
    CASE
        WHEN population IS NULL OR population <= 0 OR gdp IS NULL OR gdp <= 0 THEN NULL
        ELSE gdp / population
    END AS gdp_per_capita
FROM stg.energy_standardized
WHERE iso_code IS NOT NULL
  AND LENGTH(iso_code) = 3
  AND year IS NOT NULL;

CREATE OR REPLACE TABLE oltp.energy_source_observations AS
WITH base AS (
    SELECT
        country_name,
        iso_code,
        year,
        population,
        gdp,
        solar_electricity,
        solar_share_elec,
        wind_electricity,
        wind_share_elec,
        hydro_electricity,
        hydro_share_elec,
        coal_electricity,
        coal_share_elec,
        gas_electricity,
        gas_share_elec,
        oil_electricity,
        oil_share_elec,
        nuclear_electricity,
        nuclear_share_elec,
        biofuel_electricity,
        biofuel_share_elec,
        other_renewable_electricity,
        other_renewables_share_elec
    FROM stg.energy_standardized
    WHERE iso_code IS NOT NULL
      AND LENGTH(iso_code) = 3
      AND year IS NOT NULL
)
SELECT *
FROM (
    SELECT country_name, iso_code, year, 'solar' AS source_code, 'Solar' AS source_name,
           solar_electricity AS electricity_twh, solar_share_elec AS electricity_share_pct,
           population, gdp
    FROM base
    UNION ALL
    SELECT country_name, iso_code, year, 'wind', 'Wind',
           wind_electricity, wind_share_elec, population, gdp
    FROM base
    UNION ALL
    SELECT country_name, iso_code, year, 'hydro', 'Hydro',
           hydro_electricity, hydro_share_elec, population, gdp
    FROM base
    UNION ALL
    SELECT country_name, iso_code, year, 'biofuel', 'Biofuel',
           biofuel_electricity, biofuel_share_elec, population, gdp
    FROM base
    UNION ALL
    SELECT country_name, iso_code, year, 'other_renewable', 'Other renewable',
           other_renewable_electricity, other_renewables_share_elec, population, gdp
    FROM base
    UNION ALL
    SELECT country_name, iso_code, year, 'coal', 'Coal',
           coal_electricity, coal_share_elec, population, gdp
    FROM base
    UNION ALL
    SELECT country_name, iso_code, year, 'gas', 'Gas',
           gas_electricity, gas_share_elec, population, gdp
    FROM base
    UNION ALL
    SELECT country_name, iso_code, year, 'oil', 'Oil',
           oil_electricity, oil_share_elec, population, gdp
    FROM base
    UNION ALL
    SELECT country_name, iso_code, year, 'nuclear', 'Nuclear',
           nuclear_electricity, nuclear_share_elec, population, gdp
    FROM base
) AS long_sources
WHERE electricity_twh IS NOT NULL
   OR electricity_share_pct IS NOT NULL;

