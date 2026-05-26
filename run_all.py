"""
Projeto: Data Warehouse de Energia e Sustentabilidade
Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar
Entrega: 03/06/2026

Orquestra o projeto completo: baixa o dataset real da Our World in Data,
executa o pipeline SQL no DuckDB, exporta consultas, mede performance e gera
visualizações SVG/HTML.
"""

from __future__ import annotations

import html
import math
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

try:
    import duckdb
except ImportError as exc:
    raise SystemExit(
        "DuckDB não está instalado. Execute: pip install -r requirements.txt"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_URL = "https://owid-public.owid.io/data/energy/owid-energy-data.csv"
GIT_DATA_URL = "https://github.com/owid/energy-data.git"
RAW_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "owid-energy-data.csv"
DB_PATH = PROJECT_ROOT / "database" / "energy_dw.duckdb"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
QUERIES_DIR = OUTPUTS_DIR / "queries"
FIGURES_DIR = OUTPUTS_DIR / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"
TMP_DIR = PROJECT_ROOT / ".tmp"

SQL_PIPELINE = [
    "00_staging.sql",
    "01_oltp.sql",
    "02_dw_model.sql",
    "03_etl_load.sql",
    "04_analytics.sql",
    "05_performance.sql",
]

ANALYTICS_TABLES = [
    "analytics.q1_brazil_renewable_evolution",
    "analytics.q2_top10_renewable_latest_year",
    "analytics.q3_generation_by_group_country_latest_year",
    "analytics.q4_solar_threshold_cohort_retention",
    "analytics.q5_renewable_share_kpi_country_year",
    "analytics.validation_row_counts",
    "analytics.validation_fk_nulls",
    "analytics.validation_integrity",
    "analytics.validation_generation_by_source",
    "analytics.performance_reference_fact",
    "analytics.performance_reference_aggregated",
    "analytics.performance_benchmark",
]


def ensure_directories() -> None:
    for directory in [RAW_CSV_PATH.parent, DB_PATH.parent, QUERIES_DIR, FIGURES_DIR, DOCS_DIR, TMP_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def download_with_git_mirror() -> None:
    mirror_dir = TMP_DIR / "owid-energy-data"
    mirror_csv = mirror_dir / "owid-energy-data.csv"
    if not mirror_csv.exists():
        subprocess.run(
            [
                "git",
                "-c",
                "http.sslBackend=openssl",
                "-c",
                "http.sslVerify=false",
                "clone",
                "--depth",
                "1",
                GIT_DATA_URL,
                str(mirror_dir),
            ],
            check=True,
        )
    shutil.copyfile(mirror_csv, RAW_CSV_PATH)


def download_dataset() -> None:
    if RAW_CSV_PATH.exists() and RAW_CSV_PATH.stat().st_size > 0:
        print(f"Dataset já existe: {RAW_CSV_PATH}")
        return

    print(f"Baixando dataset real da OWID: {DATA_URL}")
    errors: list[str] = []

    if sys.platform.startswith("win"):
        output_path = str(RAW_CSV_PATH).replace("'", "''")
        powershell_command = (
            "[Net.ServicePointManager]::SecurityProtocol = "
            "[Net.SecurityProtocolType]::Tls12; "
            f"Invoke-WebRequest -UseBasicParsing -Uri '{DATA_URL}' -OutFile '{output_path}'"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", powershell_command],
                check=True,
            )
        except subprocess.CalledProcessError:
            errors.append("PowerShell Invoke-WebRequest falhou")
            print("Download via PowerShell falhou. Tentando fallback com curl.exe.")
            try:
                subprocess.run(
                    [
                        "curl.exe",
                        "-L",
                        "--retry",
                        "3",
                        "--fail",
                        DATA_URL,
                        "-o",
                        str(RAW_CSV_PATH),
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError:
                errors.append("curl.exe falhou")
                print("Download via curl.exe falhou. Tentando espelho GitHub com git.")
                download_with_git_mirror()
    else:
        try:
            with urllib.request.urlopen(DATA_URL, timeout=120) as response:
                RAW_CSV_PATH.write_bytes(response.read())
        except Exception as exc:
            errors.append(f"urllib falhou: {exc}")
            print("Download via urllib falhou. Tentando espelho GitHub com git.")
            download_with_git_mirror()

    if not RAW_CSV_PATH.exists() or RAW_CSV_PATH.stat().st_size == 0:
        detail = "; ".join(errors)
        raise RuntimeError(f"O download terminou sem gerar um CSV válido. {detail}")
    print(f"Dataset salvo em: {RAW_CSV_PATH}")


def sql_literal_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def execute_sql_pipeline(conn: duckdb.DuckDBPyConnection) -> None:
    raw_csv = sql_literal_path(RAW_CSV_PATH)
    for script_name in SQL_PIPELINE:
        script_path = SCRIPTS_DIR / script_name
        print(f"Executando {script_name}")
        sql = script_path.read_text(encoding="utf-8").replace("${RAW_CSV_PATH}", raw_csv)
        conn.execute(sql)


def run_performance_benchmark(conn: duckdb.DuckDBPyConnection, runs: int = 7) -> None:
    queries = {
        "fact_original": """
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
            ORDER BY d.year, c.country_name, s.source_group
        """,
        "aggregated_table": """
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
            ORDER BY year, country_name, source_group
        """,
    }

    rows = []
    for name, query in queries.items():
        conn.execute(query).fetchall()
        timings_ms = []
        rows_returned = 0
        for _ in range(runs):
            start = time.perf_counter()
            result = conn.execute(query).fetchall()
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings_ms.append(elapsed_ms)
            rows_returned = len(result)

        rows.append(
            {
                "query_name": name,
                "runs": runs,
                "best_ms": min(timings_ms),
                "avg_ms": sum(timings_ms) / len(timings_ms),
                "rows_returned": rows_returned,
            }
        )

    benchmark = pd.DataFrame(rows)
    conn.execute("CREATE OR REPLACE TABLE analytics.performance_benchmark AS SELECT * FROM benchmark")
    print("Benchmark de performance salvo em analytics.performance_benchmark")


def export_table(conn: duckdb.DuckDBPyConnection, table_name: str) -> None:
    safe_name = table_name.replace(".", "_")
    output_path = QUERIES_DIR / f"{safe_name}.csv"
    output_sql_path = sql_literal_path(output_path)
    conn.execute(
        f"COPY (SELECT * FROM {table_name}) TO '{output_sql_path}' "
        "(HEADER, DELIMITER ',')"
    )


def export_outputs(conn: duckdb.DuckDBPyConnection) -> None:
    for table_name in ANALYTICS_TABLES:
        export_table(conn, table_name)
    print(f"Consultas exportadas em: {QUERIES_DIR}")


def nice_number(value: float, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "n/d"
    abs_value = abs(float(value))
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f} mi"
    if abs_value >= 1_000:
        return f"{value / 1_000:.{decimals}f} mil"
    return f"{value:.{decimals}f}"


def color_for_series(series_name: str) -> str:
    palette = {
        "Solar": "#E9B44C",
        "Wind": "#3A7CA5",
        "Hydro": "#2A9D8F",
        "Renewable": "#2A9D8F",
        "Fossil": "#6C5B4C",
        "Low Carbon": "#6A4C93",
    }
    return palette.get(series_name, "#264653")


def svg_header(width: int, height: int, title: str, subtitle: str = "") -> list[str]:
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
        "<style>",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#24313d}",
        ".title{font-size:22px;font-weight:700}",
        ".subtitle{font-size:12px;fill:#62707f}",
        ".axis{stroke:#8996a3;stroke-width:1}",
        ".grid{stroke:#d9e0e6;stroke-width:1}",
        ".label{font-size:11px;fill:#62707f}",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#fbfcfd"/>',
        f'<text class="title" x="28" y="32">{html.escape(title)}</text>',
    ]
    if subtitle:
        lines.append(f'<text class="subtitle" x="28" y="52">{html.escape(subtitle)}</text>')
    return lines


def line_chart_svg(df: pd.DataFrame) -> str:
    width, height = 980, 520
    margin = {"left": 74, "right": 170, "top": 74, "bottom": 58}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]
    title = "Brasil: evolução de solar, eólica e hidrelétrica"
    subtitle = "Geração elétrica anual em TWh"
    lines = svg_header(width, height, title, subtitle)

    if df.empty:
        lines.append('<text x="40" y="110">Sem dados para exibir.</text></svg>')
        return "\n".join(lines)

    years = sorted(int(year) for year in df["year"].dropna().unique())
    min_year, max_year = min(years), max(years)
    max_y = max(float(df["electricity_twh"].max()), 1.0)
    max_y = math.ceil(max_y / 10) * 10

    def x_scale(year: float) -> float:
        if max_year == min_year:
            return margin["left"] + plot_w / 2
        return margin["left"] + ((year - min_year) / (max_year - min_year)) * plot_w

    def y_scale(value: float) -> float:
        return margin["top"] + plot_h - (value / max_y) * plot_h

    for i in range(6):
        value = max_y * i / 5
        y = y_scale(value)
        lines.append(f'<line class="grid" x1="{margin["left"]}" y1="{y:.1f}" x2="{margin["left"] + plot_w}" y2="{y:.1f}"/>')
        lines.append(f'<text class="label" x="24" y="{y + 4:.1f}">{nice_number(value, 0)}</text>')

    tick_years = years[:: max(1, len(years) // 8)]
    if years[-1] not in tick_years:
        tick_years.append(years[-1])
    for year in tick_years:
        x = x_scale(year)
        lines.append(f'<line class="grid" x1="{x:.1f}" y1="{margin["top"]}" x2="{x:.1f}" y2="{margin["top"] + plot_h}"/>')
        lines.append(f'<text class="label" text-anchor="middle" x="{x:.1f}" y="{height - 24}">{year}</text>')

    lines.append(f'<line class="axis" x1="{margin["left"]}" y1="{margin["top"] + plot_h}" x2="{margin["left"] + plot_w}" y2="{margin["top"] + plot_h}"/>')
    lines.append(f'<line class="axis" x1="{margin["left"]}" y1="{margin["top"]}" x2="{margin["left"]}" y2="{margin["top"] + plot_h}"/>')

    for index, (source, group) in enumerate(df.groupby("source_name")):
        ordered = group.sort_values("year")
        points = []
        for _, row in ordered.iterrows():
            points.append(f'{x_scale(row["year"]):.1f},{y_scale(row["electricity_twh"]):.1f}')
        color = color_for_series(str(source))
        lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}"/>')
        for _, row in ordered.iloc[:: max(1, len(ordered) // 14)].iterrows():
            lines.append(f'<circle cx="{x_scale(row["year"]):.1f}" cy="{y_scale(row["electricity_twh"]):.1f}" r="3.5" fill="{color}"/>')
        legend_y = margin["top"] + index * 26
        lines.append(f'<rect x="{width - 138}" y="{legend_y - 10}" width="14" height="14" fill="{color}"/>')
        lines.append(f'<text class="label" x="{width - 116}" y="{legend_y + 2}">{html.escape(str(source))}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def bar_chart_svg(df: pd.DataFrame) -> str:
    width, height = 980, 540
    margin = {"left": 210, "right": 44, "top": 72, "bottom": 50}
    plot_w = width - margin["left"] - margin["right"]
    bar_h = 28
    gap = 12
    title_year = int(df["year"].iloc[0]) if not df.empty else ""
    lines = svg_header(
        width,
        height,
        "Top 10 países por geração renovável",
        f"Ano mais recente disponível: {title_year}",
    )
    if df.empty:
        lines.append('<text x="40" y="110">Sem dados para exibir.</text></svg>')
        return "\n".join(lines)

    max_value = max(float(df["renewable_twh"].max()), 1.0)
    start_y = margin["top"] + 22
    for i, row in df.sort_values("renewable_twh", ascending=True).reset_index(drop=True).iterrows():
        y = start_y + i * (bar_h + gap)
        value = float(row["renewable_twh"])
        w = (value / max_value) * plot_w
        color = "#2A9D8F" if i % 2 == 0 else "#3A7CA5"
        label = html.escape(str(row["country_name"]))
        lines.append(f'<text class="label" text-anchor="end" x="{margin["left"] - 14}" y="{y + 19}">{label}</text>')
        lines.append(f'<rect x="{margin["left"]}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="3" fill="{color}"/>')
        lines.append(f'<text class="label" x="{margin["left"] + w + 8:.1f}" y="{y + 19}">{nice_number(value)} TWh</text>')

    lines.append(f'<line class="axis" x1="{margin["left"]}" y1="{start_y + 10 * (bar_h + gap)}" x2="{margin["left"] + plot_w}" y2="{start_y + 10 * (bar_h + gap)}"/>')
    lines.append("</svg>")
    return "\n".join(lines)


def interpolate_color(value: float, max_value: float) -> str:
    ratio = 0 if max_value <= 0 else max(0, min(1, value / max_value))
    start = (244, 241, 232)
    mid = (233, 180, 76)
    end = (42, 157, 143)
    if ratio < 0.5:
        local = ratio / 0.5
        rgb = tuple(round(start[i] + (mid[i] - start[i]) * local) for i in range(3))
    else:
        local = (ratio - 0.5) / 0.5
        rgb = tuple(round(mid[i] + (end[i] - mid[i]) * local) for i in range(3))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def heatmap_svg(df: pd.DataFrame) -> str:
    width, height = 1060, 560
    margin = {"left": 150, "right": 40, "top": 82, "bottom": 72}
    lines = svg_header(width, height, "Brasil: participação das fontes por ano", "% da eletricidade por fonte")
    if df.empty:
        lines.append('<text x="40" y="110">Sem dados para exibir.</text></svg>')
        return "\n".join(lines)

    recent_cutoff = int(df["year"].max()) - 29
    df = df[df["year"] >= recent_cutoff].copy()
    years = sorted(int(year) for year in df["year"].unique())
    sources = ["Hydro", "Wind", "Solar", "Biofuel", "Other renewable", "Nuclear", "Gas", "Coal", "Oil"]
    sources = [source for source in sources if source in set(df["source_name"])]
    cell_w = (width - margin["left"] - margin["right"]) / max(len(years), 1)
    cell_h = (height - margin["top"] - margin["bottom"]) / max(len(sources), 1)
    max_value = max(float(df["electricity_share_pct"].max()), 1.0)
    values = {
        (str(row["source_name"]), int(row["year"])): float(row["electricity_share_pct"])
        for _, row in df.iterrows()
        if pd.notna(row["electricity_share_pct"])
    }

    for row_index, source in enumerate(sources):
        y = margin["top"] + row_index * cell_h
        lines.append(f'<text class="label" text-anchor="end" x="{margin["left"] - 12}" y="{y + cell_h * 0.62:.1f}">{html.escape(source)}</text>')
        for col_index, year in enumerate(years):
            x = margin["left"] + col_index * cell_w
            value = values.get((source, year), 0)
            color = interpolate_color(value, max_value)
            lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w + 0.5:.1f}" height="{cell_h + 0.5:.1f}" fill="{color}"/>')
            if cell_w > 28 and cell_h > 24 and value >= max_value * 0.35:
                lines.append(f'<text class="label" text-anchor="middle" x="{x + cell_w / 2:.1f}" y="{y + cell_h * 0.62:.1f}" fill="#17333a">{value:.0f}</text>')

    tick_step = max(1, len(years) // 10)
    for col_index, year in enumerate(years):
        if col_index % tick_step == 0 or col_index == len(years) - 1:
            x = margin["left"] + col_index * cell_w + cell_w / 2
            lines.append(f'<text class="label" text-anchor="middle" x="{x:.1f}" y="{height - 34}">{year}</text>')

    legend_x = margin["left"]
    legend_y = height - 18
    for i in range(80):
        value = max_value * i / 79
        lines.append(f'<rect x="{legend_x + i * 4:.1f}" y="{legend_y - 12}" width="4.2" height="10" fill="{interpolate_color(value, max_value)}"/>')
    lines.append(f'<text class="label" x="{legend_x + 334}" y="{legend_y - 3}">0% a {max_value:.0f}%</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def save_svg(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"Gráfico salvo: {path}")


def query_dataframe(conn: duckdb.DuckDBPyConnection, query: str) -> pd.DataFrame:
    return conn.execute(query).fetchdf()


def generate_visualizations(conn: duckdb.DuckDBPyConnection) -> None:
    q1 = query_dataframe(conn, "SELECT * FROM analytics.q1_brazil_renewable_evolution")
    q2 = query_dataframe(conn, "SELECT * FROM analytics.q2_top10_renewable_latest_year")
    heatmap = query_dataframe(
        conn,
        """
        SELECT
            d.year,
            s.source_name,
            AVG(f.electricity_share_pct) AS electricity_share_pct
        FROM dw.fact_energy_generation AS f
        INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
        INNER JOIN dw.dim_country AS c ON f.country_key = c.country_key
        INNER JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
        WHERE c.country_name = 'Brazil'
          AND f.electricity_share_pct IS NOT NULL
        GROUP BY d.year, s.source_name
        ORDER BY d.year, s.source_name
        """,
    )

    line_svg = line_chart_svg(q1)
    bar_svg = bar_chart_svg(q2)
    heatmap_svg_content = heatmap_svg(heatmap)

    save_svg(FIGURES_DIR / "brazil_renewable_evolution.svg", line_svg)
    save_svg(FIGURES_DIR / "top10_renewable_latest_year.svg", bar_svg)
    save_svg(FIGURES_DIR / "brazil_source_share_heatmap.svg", heatmap_svg_content)

    generate_dashboard(conn, line_svg, bar_svg, heatmap_svg_content)


def dashboard_kpis(conn: duckdb.DuckDBPyConnection) -> dict[str, str]:
    latest_year = conn.execute(
        """
        SELECT MAX(d.year)
        FROM dw.fact_energy_generation AS f
        INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
        """
    ).fetchone()[0]

    summary = conn.execute(
        """
        SELECT
            COUNT(DISTINCT c.country_name) AS countries,
            SUM(f.electricity_twh) AS total_twh,
            100.0 * SUM(CASE WHEN s.source_group = 'Renewable' THEN f.electricity_twh ELSE 0 END)
                / NULLIF(SUM(f.electricity_twh), 0) AS renewable_share
        FROM dw.fact_energy_generation AS f
        INNER JOIN dw.dim_date AS d ON f.date_key = d.date_key
        INNER JOIN dw.dim_country AS c ON f.country_key = c.country_key
        INNER JOIN dw.dim_energy_source AS s ON f.source_key = s.source_key
        WHERE d.year = ?
        """,
        [latest_year],
    ).fetchone()

    brazil = conn.execute(
        """
        SELECT renewable_share_pct
        FROM analytics.q5_renewable_share_kpi_country_year
        WHERE country_name = 'Brazil'
          AND year = ?
        """,
        [latest_year],
    ).fetchone()

    return {
        "Ano mais recente": str(latest_year),
        "Países analisados": f"{int(summary[0])}",
        "Geração modelada": f"{nice_number(summary[1])} TWh",
        "Renováveis no total": f"{summary[2]:.1f}%",
        "Brasil renovável": f"{brazil[0]:.1f}%" if brazil else "n/d",
    }


def generate_dashboard(
    conn: duckdb.DuckDBPyConnection,
    line_svg: str,
    bar_svg: str,
    heatmap_svg_content: str,
) -> None:
    kpis = dashboard_kpis(conn)
    performance = query_dataframe(conn, "SELECT * FROM analytics.performance_benchmark ORDER BY query_name")
    performance_rows = "\n".join(
        "<tr>"
        f"<td><code>{html.escape(str(row['query_name']))}</code></td>"
        f"<td>{int(row['runs'])}</td>"
        f"<td>{row['best_ms']:.3f} ms</td>"
        f"<td>{row['avg_ms']:.3f} ms</td>"
        f"<td>{int(row['rows_returned'])}</td>"
        "</tr>"
        for _, row in performance.iterrows()
    )

    # Buscar validações de qualidade
    row_counts = query_dataframe(conn, "SELECT * FROM analytics.validation_row_counts")
    row_counts_rows = "\n".join(
        "<tr>"
        f"<td><code>{html.escape(str(row['object_name']))}</code></td>"
        f"<td>{int(row['row_count']):,}</td>"
        "</tr>"
        for _, row in row_counts.iterrows()
    )

    fk_nulls = query_dataframe(conn, "SELECT * FROM analytics.validation_fk_nulls")
    fk_null_row = fk_nulls.iloc[0]
    fk_nulls_rows = f"""<tr>
        <td>{int(fk_null_row['null_date_key'])}</td>
        <td>{int(fk_null_row['null_country_key'])}</td>
        <td>{int(fk_null_row['null_source_key'])}</td>
    </tr>"""

    integrity = query_dataframe(conn, "SELECT * FROM analytics.validation_integrity")
    integrity_rows = "\n".join(
        "<tr>"
        f"<td><code>{html.escape(str(row['relationship_name']))}</code></td>"
        f"<td>{int(row['orphan_rows'])}</td>"
        "</tr>"
        for _, row in integrity.iterrows()
    )

    kpi_cards = "\n".join(
        f'<article class="kpi"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></article>'
        for label, value in kpis.items()
    )

    dashboard_html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Data Warehouse de Energia e Sustentabilidade</title>
  <style>
    :root {{
      --ink: #1e293b;
      --muted: #64748b;
      --line: #e2e8f0;
      --bg: #f8fafc;
      --panel: #ffffff;
      --green: #2a9d8f;
      --blue: #3a7ca5;
      --gold: #e9b44c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.5;
    }}
    header {{
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 36px 24px 28px;
      text-align: center;
      box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }}
    header h1 {{
      margin: 0 0 10px;
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: #0f172a;
    }}
    header p {{
      margin: 4px 0;
      color: var(--muted);
      font-size: 15px;
    }}
    main {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 24px;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }}
    .kpi {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .kpi:hover {{
      transform: translateY(-2px);
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
    }}
    .kpis > :nth-child(1) {{ border-top: 4px solid var(--muted); }}
    .kpis > :nth-child(2) {{ border-top: 4px solid var(--blue); }}
    .kpis > :nth-child(3) {{ border-top: 4px solid var(--gold); }}
    .kpis > :nth-child(4) {{ border-top: 4px solid var(--green); }}
    .kpis > :nth-child(5) {{ border-top: 4px solid #148073; }}
    
    .kpi span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }}
    .kpi strong {{
      display: block;
      font-size: 26px;
      font-weight: 700;
      color: #0f172a;
    }}
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
      gap: 24px;
      margin-bottom: 24px;
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
      overflow: hidden;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    section:hover {{
      transform: translateY(-2px);
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
    }}
    section svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .table-wrap {{
      padding: 24px;
    }}
    h2 {{
      margin: 0 0 16px;
      font-size: 20px;
      font-weight: 700;
      color: #0f172a;
      letter-spacing: -0.3px;
    }}
    .validation-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 24px;
      margin-top: 24px;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      white-space: nowrap;
    }}
    th {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.5px;
      background: #f8fafc;
    }}
    tbody tr:hover {{
      background: #f8fafc;
    }}
    code {{
      font-family: Consolas, Monaco, monospace;
      background: #e2e8f0;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 13px;
      color: #0f172a;
    }}
    @media (max-width: 960px) {{
      .charts-grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Data Warehouse de Energia e Sustentabilidade</h1>
    <p><strong>Autores:</strong> Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar</p>
    <p><strong>Dataset:</strong> Our World in Data Energy Dataset</p>
  </header>
  <main>
    <div class="kpis">
      {kpi_cards}
    </div>
    
    <div class="charts-grid">
      <section>{line_svg}</section>
      <section>{bar_svg}</section>
    </div>
    
    <section style="margin-bottom: 24px;">{heatmap_svg_content}</section>
    
    <section class="table-wrap">
      <h2>Comparação de Performance</h2>
      <p style="margin-top: -8px; margin-bottom: 16px; font-size: 14px; color: var(--muted);">
        Benchmark comparando consultas executadas na tabela fato original vs. tabela agregada física.
      </p>
      <table>
        <thead>
          <tr>
            <th>Consulta</th>
            <th>Execuções</th>
            <th>Melhor Tempo</th>
            <th>Tempo Médio</th>
            <th>Linhas Retornadas</th>
          </tr>
        </thead>
        <tbody>{performance_rows}</tbody>
      </table>
    </section>

    <div class="validation-grid">
      <section class="table-wrap">
        <h2>Censo de Linhas</h2>
        <table>
          <thead>
            <tr>
              <th>Objeto do Banco</th>
              <th>Contagem de Linhas</th>
            </tr>
          </thead>
          <tbody>{row_counts_rows}</tbody>
        </table>
      </section>

      <section class="table-wrap">
        <h2>Integridade Referencial & Nulidades</h2>
        <h3 style="font-size: 14px; margin-top: 0; margin-bottom: 10px; color: var(--muted); font-weight: 600;">Chaves Estrangeiras Nulas na Fato</h3>
        <table style="margin-bottom: 24px;">
          <thead>
            <tr>
              <th>null_date_key</th>
              <th>null_country_key</th>
              <th>null_source_key</th>
            </tr>
          </thead>
          <tbody>{fk_nulls_rows}</tbody>
        </table>

        <h3 style="font-size: 14px; margin-top: 0; margin-bottom: 10px; color: var(--muted); font-weight: 600;">Registros Órfãos (Violadores de FK)</h3>
        <table>
          <thead>
            <tr>
              <th>Relacionamento</th>
              <th>Linhas Órfãs</th>
            </tr>
          </thead>
          <tbody>{integrity_rows}</tbody>
        </table>
      </section>
    </div>
  </main>
</body>
</html>
"""
    output_dashboard = OUTPUTS_DIR / "dashboard.html"
    root_dashboard = PROJECT_ROOT / "dashboard.html"
    output_dashboard.write_text(dashboard_html, encoding="utf-8")
    shutil.copyfile(output_dashboard, root_dashboard)
    print(f"Dashboard salvo em: {output_dashboard}")
    print(f"Cópia do dashboard salva em: {root_dashboard}")


def write_performance_summary(conn: duckdb.DuckDBPyConnection) -> None:
    benchmark = query_dataframe(conn, "SELECT * FROM analytics.performance_benchmark ORDER BY query_name")
    if benchmark.empty:
        return

    fact = benchmark[benchmark["query_name"] == "fact_original"].iloc[0]
    agg = benchmark[benchmark["query_name"] == "aggregated_table"].iloc[0]
    gain = fact["avg_ms"] / agg["avg_ms"] if agg["avg_ms"] > 0 else float("nan")
    summary = f"""# Resultados de Performance

Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar

Medição gerada automaticamente por `run_all.py` a partir do dataset real da Our World in Data.

| Consulta | Execuções | Melhor ms | Média ms | Linhas |
|---|---:|---:|---:|---:|
| Fato original | {int(fact['runs'])} | {fact['best_ms']:.3f} | {fact['avg_ms']:.3f} | {int(fact['rows_returned'])} |
| Tabela agregada | {int(agg['runs'])} | {agg['best_ms']:.3f} | {agg['avg_ms']:.3f} | {int(agg['rows_returned'])} |

Ganho médio observado: {gain:.2f}x quando a consulta usa `dw.fact_energy_generation_annual_grouped`.
"""
    (OUTPUTS_DIR / "performance_summary.md").write_text(summary, encoding="utf-8")


def main() -> None:
    ensure_directories()
    download_dataset()

    conn = duckdb.connect(str(DB_PATH))
    try:
        execute_sql_pipeline(conn)
        run_performance_benchmark(conn)
        export_outputs(conn)
        generate_visualizations(conn)
        write_performance_summary(conn)
    finally:
        conn.close()

    print("Pipeline concluído com sucesso.")

    try:
        import webbrowser
        from pathlib import Path

        dashboard_path = Path("outputs/dashboard.html").resolve()

        print("Abrindo dashboard HTML no navegador padrão...")
        webbrowser.open(dashboard_path.as_uri())

    except Exception as e:
        print(f"Não foi possível abrir o dashboard automaticamente: {e}")


if __name__ == "__main__":
    main()
