-- Projeto: Data Warehouse de Energia e Sustentabilidade
-- Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar
-- Entrega: 03/06/2026
-- Etapa 05: cria tabela agregada anual e consultas de referência para comparação de performance.

CREATE OR REPLACE TABLE dw.fact_energy_generation_annual_grouped AS
SELECT
    d.year,
    c.country_name,
    s.source_group,
    SUM(f.electricity_twh) AS electricity_twh
FROM dw.fact_energy_generation AS f
INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
INNER JOIN dw.dim_country AS c ON f.country_key = c.country_key
INNER JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
GROUP BY d.year, c.country_name, s.source_group;

CREATE OR REPLACE TABLE analytics.performance_reference_fact AS
WITH latest_year AS (
    SELECT MAX(d.year) AS year
    FROM dw.fact_energy_generation AS f
    INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
)
SELECT
    d.year,
    c.country_name,
    s.source_group,
    SUM(f.electricity_twh) AS electricity_twh
FROM dw.fact_energy_generation AS f
INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
INNER JOIN dw.dim_country AS c ON f.country_key = c.country_key
INNER JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
WHERE d.year = (SELECT year FROM latest_year)
GROUP BY d.year, c.country_name, s.source_group
ORDER BY d.year, c.country_name, s.source_group;

CREATE OR REPLACE TABLE analytics.performance_reference_aggregated AS
WITH latest_year AS (
    SELECT MAX(year) AS year
    FROM dw.fact_energy_generation_annual_grouped
)
SELECT
    year,
    country_name,
    source_group,
    electricity_twh
FROM dw.fact_energy_generation_annual_grouped
WHERE year = (SELECT year FROM latest_year)
ORDER BY year, country_name, source_group;

