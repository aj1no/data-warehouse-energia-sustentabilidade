-- Projeto: Data Warehouse de Energia e Sustentabilidade
-- Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar
-- Entrega: 03/06/2026
-- Etapa 03: carrega dimensões e fato. A dim_country implementa SCD Type 2 por faixas.

INSERT INTO dw.dim_date (date_key, year, decade, year_start_date)
SELECT
    (year * 10000) + 101 AS date_key,
    year,
    FLOOR(year / 10) * 10 AS decade,
    MAKE_DATE(year, 1, 1) AS year_start_date
FROM generate_series(
    (SELECT MIN(year) FROM oltp.country_year_metrics),
    (SELECT MAX(year) FROM oltp.country_year_metrics)
) AS years(year);

INSERT INTO dw.dim_energy_source (
    source_key,
    source_code,
    source_name,
    source_group,
    is_renewable,
    is_low_carbon
)
VALUES
    (1, 'solar', 'Solar', 'Renewable', true, true),
    (2, 'wind', 'Wind', 'Renewable', true, true),
    (3, 'hydro', 'Hydro', 'Renewable', true, true),
    (4, 'biofuel', 'Biofuel', 'Renewable', true, true),
    (5, 'other_renewable', 'Other renewable', 'Renewable', true, true),
    (6, 'coal', 'Coal', 'Fossil', false, false),
    (7, 'gas', 'Gas', 'Fossil', false, false),
    (8, 'oil', 'Oil', 'Fossil', false, false),
    (9, 'nuclear', 'Nuclear', 'Low Carbon', false, true);

INSERT INTO dw.dim_country (
    country_key,
    country_name,
    iso_code,
    population_band,
    gdp_per_capita_band,
    start_year,
    end_year,
    is_current
)
WITH ordered AS (
    SELECT
        country_name,
        iso_code,
        year,
        population_band,
        gdp_per_capita_band,
        LAG(population_band) OVER (
            PARTITION BY country_name, iso_code
            ORDER BY year
        ) AS previous_population_band,
        LAG(gdp_per_capita_band) OVER (
            PARTITION BY country_name, iso_code
            ORDER BY year
        ) AS previous_gdp_per_capita_band
    FROM oltp.country_year_metrics
),
change_flags AS (
    SELECT
        *,
        CASE
            WHEN previous_population_band IS NULL THEN 1
            WHEN previous_population_band <> population_band THEN 1
            WHEN previous_gdp_per_capita_band <> gdp_per_capita_band THEN 1
            ELSE 0
        END AS new_version_flag
    FROM ordered
),
versioned AS (
    SELECT
        *,
        SUM(new_version_flag) OVER (
            PARTITION BY country_name, iso_code
            ORDER BY year
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS version_number
    FROM change_flags
),
scd_ranges AS (
    SELECT
        country_name,
        iso_code,
        population_band,
        gdp_per_capita_band,
        MIN(year) AS start_year,
        MAX(year) AS end_year
    FROM versioned
    GROUP BY
        country_name,
        iso_code,
        population_band,
        gdp_per_capita_band,
        version_number
),
numbered AS (
    SELECT
        ROW_NUMBER() OVER (
            ORDER BY country_name, iso_code, start_year, end_year
        ) AS country_key,
        *,
        ROW_NUMBER() OVER (
            PARTITION BY country_name, iso_code
            ORDER BY end_year DESC, start_year DESC
        ) AS current_rank
    FROM scd_ranges
)
SELECT
    country_key,
    country_name,
    iso_code,
    population_band,
    gdp_per_capita_band,
    start_year,
    end_year,
    current_rank = 1 AS is_current
FROM numbered;

INSERT INTO dw.fact_energy_generation (
    date_key,
    country_key,
    source_key,
    electricity_twh,
    electricity_share_pct,
    population,
    gdp,
    created_at
)
SELECT
    d.date_key,
    c.country_key,
    s.source_key,
    o.electricity_twh,
    o.electricity_share_pct,
    o.population,
    o.gdp,
    CURRENT_TIMESTAMP AS created_at
FROM oltp.energy_source_observations AS o
INNER JOIN dw.dim_date AS d
    ON o.year = d.year
INNER JOIN dw.dim_country AS c
    ON o.country_name = c.country_name
   AND o.iso_code = c.iso_code
   AND o.year BETWEEN c.start_year AND c.end_year
INNER JOIN dw.dim_energy_source AS s
    ON o.source_code = s.source_code
WHERE o.electricity_twh IS NOT NULL;

