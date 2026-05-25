-- Projeto: Data Warehouse de Energia e Sustentabilidade
-- Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar
-- Entrega: 03/06/2026
-- Etapa 04: consultas analíticas obrigatórias e validações de qualidade.
-- Arquivo revisado para leitura acadêmica e compatibilidade com DuckDB.

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE TABLE analytics.q1_brazil_renewable_evolution AS
SELECT
    d.year,
    s.source_name,
    SUM(f.electricity_twh) AS electricity_twh
FROM dw.fact_energy_generation AS f
INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
INNER JOIN dw.dim_country AS c ON f.country_key = c.country_key
INNER JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
WHERE c.country_name = 'Brazil'
  AND s.source_name IN ('Solar', 'Wind', 'Hydro')
GROUP BY d.year, s.source_name
ORDER BY d.year, s.source_name;

CREATE OR REPLACE TABLE analytics.q2_top10_renewable_latest_year AS
WITH latest_year AS (
    SELECT MAX(d.year) AS year
    FROM dw.fact_energy_generation AS f
    INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
)
SELECT
    d.year,
    c.country_name,
    SUM(f.electricity_twh) AS renewable_twh
FROM dw.fact_energy_generation AS f
INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
INNER JOIN dw.dim_country AS c ON f.country_key = c.country_key
INNER JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
WHERE d.year = (SELECT year FROM latest_year)
  AND s.source_group = 'Renewable'
GROUP BY d.year, c.country_name
ORDER BY renewable_twh DESC
LIMIT 10;

CREATE OR REPLACE TABLE analytics.q3_generation_by_group_country_latest_year AS
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

CREATE OR REPLACE TABLE analytics.q4_solar_threshold_cohort_retention AS
WITH solar AS (
    SELECT
        c.country_name,
        d.year,
        f.electricity_share_pct AS solar_share_pct
    FROM dw.fact_energy_generation AS f
    INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
    INNER JOIN dw.dim_country AS c ON f.country_key = c.country_key
    INNER JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
    WHERE s.source_code = 'solar'
      AND f.electricity_share_pct IS NOT NULL
),
first_crossing AS (
    SELECT
        country_name,
        MIN(year) AS cohort_year
    FROM solar
    WHERE solar_share_pct >= 1
    GROUP BY country_name
),
cohort_sizes AS (
    SELECT
        cohort_year,
        COUNT(DISTINCT country_name) AS cohort_size
    FROM first_crossing
    GROUP BY cohort_year
),
retention AS (
    SELECT
        f.cohort_year,
        s.year - f.cohort_year AS years_since_threshold,
        COUNT(DISTINCT CASE WHEN s.solar_share_pct >= 1 THEN s.country_name END) AS retained_countries
    FROM first_crossing AS f
    INNER JOIN solar AS s
        ON f.country_name = s.country_name
       AND s.year >= f.cohort_year
    GROUP BY f.cohort_year, s.year - f.cohort_year
)
SELECT
    r.cohort_year,
    r.years_since_threshold,
    cs.cohort_size,
    r.retained_countries,
    ROUND(100.0 * r.retained_countries / NULLIF(cs.cohort_size, 0), 2) AS retention_pct
FROM retention AS r
INNER JOIN cohort_sizes AS cs ON r.cohort_year = cs.cohort_year
ORDER BY r.cohort_year, r.years_since_threshold;

CREATE OR REPLACE TABLE analytics.q5_renewable_share_kpi_country_year AS
SELECT
    d.year,
    c.country_name,
    SUM(CASE WHEN s.source_group = 'Renewable' THEN f.electricity_twh ELSE 0 END) AS renewable_twh,
    SUM(f.electricity_twh) AS total_modeled_twh,
    ROUND(
        100.0 * SUM(CASE WHEN s.source_group = 'Renewable' THEN f.electricity_twh ELSE 0 END)
        / NULLIF(SUM(f.electricity_twh), 0),
        2
    ) AS renewable_share_pct
FROM dw.fact_energy_generation AS f
INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
INNER JOIN dw.dim_country AS c ON f.country_key = c.country_key
INNER JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
GROUP BY d.year, c.country_name
HAVING SUM(f.electricity_twh) > 0
ORDER BY d.year, c.country_name;

CREATE OR REPLACE TABLE analytics.validation_row_counts AS
SELECT 'stg.energy_raw' AS object_name, COUNT(*) AS row_count FROM stg.energy_raw
UNION ALL
SELECT 'stg.energy_standardized', COUNT(*) FROM stg.energy_standardized
UNION ALL
SELECT 'oltp.country_year_metrics', COUNT(*) FROM oltp.country_year_metrics
UNION ALL
SELECT 'oltp.energy_source_observations', COUNT(*) FROM oltp.energy_source_observations
UNION ALL
SELECT 'dw.dim_date', COUNT(*) FROM dw.dim_date
UNION ALL
SELECT 'dw.dim_country', COUNT(*) FROM dw.dim_country
UNION ALL
SELECT 'dw.dim_energy_source', COUNT(*) FROM dw.dim_energy_source
UNION ALL
SELECT 'dw.fact_energy_generation', COUNT(*) FROM dw.fact_energy_generation;

CREATE OR REPLACE TABLE analytics.validation_fk_nulls AS
SELECT
    SUM(CASE WHEN date_key IS NULL THEN 1 ELSE 0 END) AS null_date_key,
    SUM(CASE WHEN country_key IS NULL THEN 1 ELSE 0 END) AS null_country_key,
    SUM(CASE WHEN source_key IS NULL THEN 1 ELSE 0 END) AS null_source_key
FROM dw.fact_energy_generation;

CREATE OR REPLACE TABLE analytics.validation_integrity AS
SELECT
    'fact_to_dim_date' AS relationship_name,
    COUNT(*) AS orphan_rows
FROM dw.fact_energy_generation AS f
LEFT JOIN dw.dim_date AS d ON f.date_key = d.date_key
WHERE d.date_key IS NULL
UNION ALL
SELECT
    'fact_to_dim_country',
    COUNT(*)
FROM dw.fact_energy_generation AS f
LEFT JOIN dw.dim_country AS c ON f.country_key = c.country_key
WHERE c.country_key IS NULL
UNION ALL
SELECT
    'fact_to_dim_energy_source',
    COUNT(*)
FROM dw.fact_energy_generation AS f
LEFT JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
WHERE s.source_key IS NULL;

CREATE OR REPLACE TABLE analytics.validation_generation_by_source AS
SELECT
    s.source_name,
    s.source_group,
    ROUND(SUM(f.electricity_twh), 4) AS total_electricity_twh
FROM dw.fact_energy_generation AS f
INNER JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
GROUP BY s.source_name, s.source_group
ORDER BY s.source_group, s.source_name;
