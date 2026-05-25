-- Projeto: Data Warehouse de Energia e Sustentabilidade
-- Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar
-- Entrega: 03/06/2026
-- Etapa 02: define o modelo dimensional em estrela no schema dw.
-- Arquivo revisado para leitura acadêmica e compatibilidade com DuckDB.

CREATE SCHEMA IF NOT EXISTS dw;

DROP TABLE IF EXISTS dw.fact_energy_generation_annual_grouped;
DROP TABLE IF EXISTS dw.fact_energy_generation;
DROP TABLE IF EXISTS dw.dim_energy_source;
DROP TABLE IF EXISTS dw.dim_country;
DROP TABLE IF EXISTS dw.dim_date;

CREATE TABLE dw.dim_date (
    date_key INTEGER PRIMARY KEY,
    year INTEGER NOT NULL UNIQUE,
    decade INTEGER NOT NULL,
    year_start_date DATE NOT NULL
);

CREATE TABLE dw.dim_country (
    country_key BIGINT PRIMARY KEY,
    country_name VARCHAR NOT NULL,
    iso_code VARCHAR NOT NULL,
    population_band VARCHAR NOT NULL,
    gdp_per_capita_band VARCHAR NOT NULL,
    start_year INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    is_current BOOLEAN NOT NULL
);

CREATE TABLE dw.dim_energy_source (
    source_key INTEGER PRIMARY KEY,
    source_code VARCHAR NOT NULL UNIQUE,
    source_name VARCHAR NOT NULL,
    source_group VARCHAR NOT NULL,
    is_renewable BOOLEAN NOT NULL,
    is_low_carbon BOOLEAN NOT NULL
);

CREATE TABLE dw.fact_energy_generation (
    date_key INTEGER NOT NULL,
    country_key BIGINT NOT NULL,
    source_key INTEGER NOT NULL,
    electricity_twh DOUBLE,
    electricity_share_pct DOUBLE,
    population DOUBLE,
    gdp DOUBLE,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (date_key, country_key, source_key)
);
