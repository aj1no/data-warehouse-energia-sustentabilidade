"""
Projeto: Data Warehouse de Energia e Sustentabilidade
Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar
Entrega: 03/06/2026

Gera artefatos finais de entrega pelo GitHub, com arquivos normalizados:
- docs/relatorio_tecnico.pdf
- docs/diagrama_modelo_estrela.png
"""

from __future__ import annotations

import csv
import re
import sys
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as ReportImage,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.pdfgen import canvas


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
QUERIES_DIR = OUTPUTS_DIR / "queries"
DB_PATH = PROJECT_ROOT / "database" / "energy_dw.duckdb"
REPORT_MD = DOCS_DIR / "relatorio_tecnico.md"
REPORT_PDF = DOCS_DIR / "relatorio_tecnico.pdf"
DIAGRAM_PNG = DOCS_DIR / "diagrama_modelo_estrela.png"
LINE_CHART_PNG = FIGURES_DIR / "brazil_renewable_evolution.png"
BAR_CHART_PNG = FIGURES_DIR / "top10_renewable_latest_year.png"
HEATMAP_PNG = FIGURES_DIR / "brazil_source_share_heatmap.png"


def clean_inline_markdown(text: str) -> str:
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


def paragraph_from_markdown(line: str, styles) -> Paragraph:
    stripped = line.strip()
    if stripped.startswith("# "):
        return Paragraph(clean_inline_markdown(stripped[2:]), styles["Title"])
    if stripped.startswith("## "):
        return Paragraph(clean_inline_markdown(stripped[3:]), styles["Heading2"])
    if stripped.startswith("### "):
        return Paragraph(clean_inline_markdown(stripped[4:]), styles["Heading3"])
    return Paragraph(clean_inline_markdown(stripped), styles["BodyText"])


def markdown_table_to_reportlab(lines: list[str], styles) -> Table:
    rows = []
    for line in lines:
        if re.match(r"^\|\s*:?-{3,}", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append([Paragraph(clean_inline_markdown(cell), styles["TableCell"]) for cell in cells])

    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24313d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b7c0c8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7f9")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def report_image_flowable(path: Path, max_width: float = 16.0 * cm, max_height: float = 9.5 * cm) -> ReportImage:
    with Image.open(path) as image:
        width, height = image.size
    scale = min(max_width / width, max_height / height, 1)
    return ReportImage(str(path), width=width * scale, height=height * scale)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        # ABNT: capa (pagina 1) e folha de rosto (pagina 2) nao possuem numeracao.
        # Paginas pre-textuais contam na numeracao, mas a numeracao so eh exibida a partir da Introducao (pagina 6)
        # no canto superior direito (2cm da borda superior e 2cm da borda direita).
        if self._pageNumber >= 6:
            self.saveState()
            self.setFont("Helvetica", 10)
            self.drawRightString(21.0 * cm - 2.0 * cm, 29.7 * cm - 2.0 * cm, str(self._pageNumber))
            self.restoreState()


def generate_report_pdf() -> None:
    styles = getSampleStyleSheet()
    
    # Customizacao de estilos existentes
    styles["Title"].fontSize = 14
    styles["Title"].leading = 18
    styles["Title"].alignment = 1 # Centralizado
    styles["Title"].fontName = "Helvetica-Bold"
    styles["Title"].firstLineIndent = 0
    styles["Title"].spaceAfter = 12

    styles["Heading2"].fontSize = 12
    styles["Heading2"].leading = 16
    styles["Heading2"].fontName = "Helvetica-Bold"
    styles["Heading2"].firstLineIndent = 0
    styles["Heading2"].spaceBefore = 14
    styles["Heading2"].spaceAfter = 8

    styles["Heading3"].fontSize = 12
    styles["Heading3"].leading = 16
    styles["Heading3"].fontName = "Helvetica-BoldOblique"
    styles["Heading3"].firstLineIndent = 0
    styles["Heading3"].spaceBefore = 12
    styles["Heading3"].spaceAfter = 6

    styles["BodyText"].fontSize = 12
    styles["BodyText"].leading = 18 # Espacamento 1.5 (12 * 1.5 = 18)
    styles["BodyText"].alignment = 4 # Justificado
    styles["BodyText"].firstLineIndent = 1.25 * cm
    styles["BodyText"].spaceAfter = 8

    # Novos estilos customizados
    styles.add(ParagraphStyle(
        name="TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        firstLineIndent=0,
    ))

    styles.add(ParagraphStyle(
        name="SubmissionNote",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        leftIndent=8 * cm,
        alignment=4, # Justificado
        firstLineIndent=0,
        spaceBefore=12,
        spaceAfter=12,
    ))

    styles.add(ParagraphStyle(
        name="CenteredText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        alignment=1, # Centralizado
        firstLineIndent=0,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        name="FigureCaption",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        alignment=1,
        firstLineIndent=0,
        spaceBefore=8,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="PreTextualBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        alignment=4, # Justificado
        firstLineIndent=1.25 * cm,
        spaceAfter=8,
    ))

    story = []
    lines = REPORT_MD.read_text(encoding="utf-8").splitlines()
    
    page_count = 1
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Quebra de pagina
        if line.strip() == "---":
            story.append(PageBreak())
            page_count += 1
            i += 1
            continue

        # Espacadores verticais
        if "<br/>" in line:
            count = line.count("<br/>")
            story.append(Spacer(1, count * 0.5 * cm))
            i += 1
            continue

        # Nota de submissao (Folha de rosto)
        if line.strip().startswith("<p align=\"right\">") or line.strip().startswith("<p align='right'>"):
            note_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().endswith("</p>"):
                note_lines.append(lines[i].strip())
                i += 1
            if i < len(lines):
                note_lines.append(lines[i].strip().replace("</p>", ""))
                i += 1
            note_text = " ".join(note_lines).replace("<br/>", " ")
            story.append(Paragraph(note_text, styles["SubmissionNote"]))
            continue

        # Ignorar linhas vazias
        if not line.strip():
            i += 1
            continue

        image_match = re.match(r"^!\[(.+?)\]\((.+?)\)$", line.strip())
        if image_match:
            caption, relative_path = image_match.groups()
            image_path = PROJECT_ROOT / relative_path
            if image_path.exists():
                story.append(Paragraph(clean_inline_markdown(caption), styles["FigureCaption"]))
                story.append(report_image_flowable(image_path))
                story.append(Spacer(1, 0.25 * cm))
            else:
                story.append(Paragraph(clean_inline_markdown(f"{caption} (imagem não encontrada)"), styles["FigureCaption"]))
            i += 1
            continue

        # Tabelas Markdown
        if line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            story.append(markdown_table_to_reportlab(table_lines, styles))
            story.append(Spacer(1, 0.15 * cm))
            continue

        # Listas com marcador
        if line.strip().startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                text = lines[i].strip()[2:]
                items.append(ListItem(Paragraph(clean_inline_markdown(text), styles["BodyText"])))
                i += 1
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=16))
            story.append(Spacer(1, 0.1 * cm))
            continue

        # Blocos de codigo
        if line.strip().startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            code_text = "<br/>".join(l.replace(" ", "&nbsp;") for l in code_lines)
            story.append(Paragraph(f"<font name='Courier'>{code_text}</font>", styles["TableCell"]))
            story.append(Spacer(1, 0.1 * cm))
            continue

        # Paragrafos normais e titulos
        stripped = line.strip()
        if page_count <= 2:
            # Paginas 1 e 2: Centraliza todo o texto (Capa e Folha de rosto)
            text = stripped.lstrip("#").strip()
            story.append(Paragraph(clean_inline_markdown(text), styles["CenteredText"]))
        else:
            # Demais paginas (Resumo, Sumario e capitulos)
            if stripped.startswith("# "):
                text = stripped[2:]
                style = styles["Title"] if page_count <= 4 else styles["Heading2"]
                story.append(Paragraph(clean_inline_markdown(text), style))
            elif stripped.startswith("## "):
                story.append(Paragraph(clean_inline_markdown(stripped[3:]), styles["Heading2"]))
            elif stripped.startswith("### "):
                story.append(Paragraph(clean_inline_markdown(stripped[4:]), styles["Heading3"]))
            else:
                # No resumo e no abstract, nao queremos recuo de paragrafo ABNT.
                style = styles["PreTextualBody"] if page_count in (3, 4) else styles["BodyText"]
                story.append(Paragraph(clean_inline_markdown(stripped), style))
                
        i += 1

    # Margens ABNT: Superior: 3cm, Esquerda: 3cm, Inferior: 2cm, Direita: 2cm
    doc = SimpleDocTemplate(
        str(REPORT_PDF),
        pagesize=A4,
        leftMargin=3.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=3.0 * cm,
        bottomMargin=2.0 * cm,
        title="Relatório Técnico - Data Warehouse de Energia e Sustentabilidade",
        author="Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar",
    )
    doc.build(story, canvasmaker=NumberedCanvas)


def get_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def draw_chart_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str | None = None) -> None:
    draw.text((48, 34), title, font=get_font(30, bold=True), fill="#17212b")
    if subtitle:
        draw.text((48, 76), subtitle, font=get_font(18), fill="#526171")


def report_color_for_source(source: str) -> str:
    return {
        "Solar": "#e9b44c",
        "Wind": "#3a7ca5",
        "Hydro": "#2a9d8f",
        "Biofuel": "#5a9e6f",
        "Other renewable": "#7cb7a8",
        "Nuclear": "#6a4c93",
        "Gas": "#8b6f47",
        "Coal": "#5a4a42",
        "Oil": "#9a6b59",
    }.get(source, "#264653")


def interpolate_report_color(value: float, max_value: float) -> tuple[int, int, int]:
    ratio = 0 if max_value <= 0 else max(0, min(1, value / max_value))
    start = (244, 241, 232)
    mid = (233, 180, 76)
    end = (42, 157, 143)
    if ratio < 0.5:
        local = ratio / 0.5
        return tuple(round(start[i] + (mid[i] - start[i]) * local) for i in range(3))
    local = (ratio - 0.5) / 0.5
    return tuple(round(mid[i] + (end[i] - mid[i]) * local) for i in range(3))


def generate_line_chart_png() -> None:
    rows = read_csv_rows(QUERIES_DIR / "analytics_q1_brazil_renewable_evolution.csv")
    width, height = 1400, 760
    image = Image.new("RGB", (width, height), "#fbfcfd")
    draw = ImageDraw.Draw(image)
    draw_chart_title(draw, "Brasil: evolução de solar, eólica e hidrelétrica", "Geração elétrica anual em TWh")

    if not rows:
        draw.text((60, 140), "Sem dados para exibir.", font=get_font(22), fill="#526171")
        image.save(LINE_CHART_PNG)
        return

    margin = {"left": 105, "right": 240, "top": 125, "bottom": 82}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]
    years = sorted({int(row["year"]) for row in rows})
    values = [float(row["electricity_twh"]) for row in rows]
    max_y = max(10, int(max(values) / 10 + 1) * 10)

    def x_scale(year: int) -> float:
        return margin["left"] + ((year - years[0]) / max(years[-1] - years[0], 1)) * plot_w

    def y_scale(value: float) -> float:
        return margin["top"] + plot_h - (value / max_y) * plot_h

    axis_font = get_font(17)
    for index in range(6):
        value = max_y * index / 5
        y = y_scale(value)
        draw.line((margin["left"], y, margin["left"] + plot_w, y), fill="#d9e0e6", width=1)
        draw.text((30, y - 10), f"{value:.0f}", font=axis_font, fill="#526171")
    tick_step = max(1, len(years) // 8)
    for index, year in enumerate(years):
        if index % tick_step == 0 or year == years[-1]:
            x = x_scale(year)
            draw.line((x, margin["top"], x, margin["top"] + plot_h), fill="#eef2f5", width=1)
            draw.text((x - 22, height - 50), str(year), font=axis_font, fill="#526171")

    draw.line((margin["left"], margin["top"] + plot_h, margin["left"] + plot_w, margin["top"] + plot_h), fill="#8996a3", width=2)
    draw.line((margin["left"], margin["top"], margin["left"], margin["top"] + plot_h), fill="#8996a3", width=2)

    grouped: dict[str, list[tuple[int, float]]] = {}
    for row in rows:
        grouped.setdefault(row["source_name"], []).append((int(row["year"]), float(row["electricity_twh"])))
    for legend_index, source in enumerate(["Hydro", "Solar", "Wind"]):
        points = [(x_scale(year), y_scale(value)) for year, value in sorted(grouped.get(source, []))]
        if len(points) >= 2:
            draw.line(points, fill=report_color_for_source(source), width=5, joint="curve")
        for point in points[:: max(1, len(points) // 12)]:
            x, y = point
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=report_color_for_source(source))
        legend_y = margin["top"] + legend_index * 34
        draw.rectangle((width - 190, legend_y - 12, width - 166, legend_y + 12), fill=report_color_for_source(source))
        draw.text((width - 155, legend_y - 11), source, font=get_font(18), fill="#24313d")

    image.save(LINE_CHART_PNG)


def generate_bar_chart_png() -> None:
    rows = read_csv_rows(QUERIES_DIR / "analytics_q2_top10_renewable_latest_year.csv")
    width, height = 1400, 780
    image = Image.new("RGB", (width, height), "#fbfcfd")
    draw = ImageDraw.Draw(image)
    year = rows[0]["year"] if rows else ""
    draw_chart_title(draw, "Top 10 países por geração renovável", f"Ano mais recente disponível: {year}")

    if not rows:
        draw.text((60, 140), "Sem dados para exibir.", font=get_font(22), fill="#526171")
        image.save(BAR_CHART_PNG)
        return

    rows = sorted(rows, key=lambda row: float(row["renewable_twh"]))
    max_value = max(float(row["renewable_twh"]) for row in rows)
    left, top, plot_w = 285, 125, 980
    bar_h, gap = 40, 18
    font = get_font(19)
    for index, row in enumerate(rows):
        y = top + index * (bar_h + gap)
        value = float(row["renewable_twh"])
        bar_w = (value / max_value) * plot_w
        color = "#2a9d8f" if index % 2 == 0 else "#3a7ca5"
        draw.text((45, y + 8), row["country_name"], font=font, fill="#24313d")
        draw.rounded_rectangle((left, y, left + bar_w, y + bar_h), radius=5, fill=color)
        draw.text((left + bar_w + 12, y + 8), f"{value:,.0f} TWh".replace(",", "."), font=font, fill="#526171")
    draw.line((left, top + len(rows) * (bar_h + gap), left + plot_w, top + len(rows) * (bar_h + gap)), fill="#8996a3", width=2)
    image.save(BAR_CHART_PNG)


def generate_heatmap_png() -> None:
    width, height = 1500, 760
    image = Image.new("RGB", (width, height), "#fbfcfd")
    draw = ImageDraw.Draw(image)
    draw_chart_title(draw, "Brasil: participação das fontes por ano", "% da eletricidade por fonte")

    if not DB_PATH.exists():
        draw.text((60, 140), "Banco DuckDB não encontrado.", font=get_font(22), fill="#526171")
        image.save(HEATMAP_PNG)
        return

    import duckdb

    with duckdb.connect(str(DB_PATH), read_only=True) as conn:
        rows = conn.execute(
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
            """
        ).fetchall()

    if not rows:
        draw.text((60, 140), "Sem dados para exibir.", font=get_font(22), fill="#526171")
        image.save(HEATMAP_PNG)
        return

    max_year = max(int(row[0]) for row in rows)
    recent_cutoff = max_year - 29
    rows = [row for row in rows if int(row[0]) >= recent_cutoff]
    years = sorted({int(row[0]) for row in rows})
    sources = ["Hydro", "Wind", "Solar", "Biofuel", "Other renewable", "Nuclear", "Gas", "Coal", "Oil"]
    present_sources = {str(row[1]) for row in rows}
    sources = [source for source in sources if source in present_sources]
    values = {(str(source), int(year)): float(value or 0) for year, source, value in rows}
    max_value = max(values.values()) if values else 1

    left, top = 235, 125
    plot_w, plot_h = 1180, 510
    cell_w = plot_w / max(len(years), 1)
    cell_h = plot_h / max(len(sources), 1)
    label_font = get_font(17)
    for row_index, source in enumerate(sources):
        y = top + row_index * cell_h
        draw.text((45, y + cell_h * 0.35), source, font=label_font, fill="#24313d")
        for col_index, year in enumerate(years):
            x = left + col_index * cell_w
            value = values.get((source, year), 0)
            draw.rectangle((x, y, x + cell_w + 1, y + cell_h + 1), fill=interpolate_report_color(value, max_value))

    tick_step = max(1, len(years) // 10)
    for index, year in enumerate(years):
        if index % tick_step == 0 or year == years[-1]:
            x = left + index * cell_w + cell_w / 2
            draw.text((x - 22, height - 78), str(year), font=label_font, fill="#526171")
    image.save(HEATMAP_PNG)


def generate_report_figure_pngs() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    generate_line_chart_png()
    generate_bar_chart_png()
    generate_heatmap_png()


def draw_box(draw: ImageDraw.ImageDraw, xy, title: str, fields: list[str], fill: str, outline: str) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=12, fill=fill, outline=outline, width=3)
    draw.text((x1 + 18, y1 + 14), title, font=get_font(26, bold=True), fill="#17212b")
    y = y1 + 55
    for field in fields:
        draw.text((x1 + 22, y), field, font=get_font(18), fill="#24313d")
        y += 28


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = "#3a7ca5") -> None:
    draw.line([start, end], fill=color, width=4)
    ex, ey = end
    sx, sy = start
    if ex > sx:
        points = [(ex, ey), (ex - 14, ey - 8), (ex - 14, ey + 8)]
    elif ex < sx:
        points = [(ex, ey), (ex + 14, ey - 8), (ex + 14, ey + 8)]
    elif ey > sy:
        points = [(ex, ey), (ex - 8, ey - 14), (ex + 8, ey - 14)]
    else:
        points = [(ex, ey), (ex - 8, ey + 14), (ex + 8, ey + 14)]
    draw.polygon(points, fill=color)


def generate_star_schema_png() -> None:
    width, height = 1600, 1050
    image = Image.new("RGB", (width, height), "#f4f7f9")
    draw = ImageDraw.Draw(image)

    draw.text(
        (60, 40),
        "Modelo Estrela - Data Warehouse de Energia e Sustentabilidade",
        font=get_font(38, bold=True),
        fill="#17212b",
    )
    draw.text(
        (60, 92),
        "Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar",
        font=get_font(22),
        fill="#526171",
    )

    fact = (540, 390, 1060, 700)
    dim_date = (80, 150, 470, 380)
    dim_country = (80, 680, 500, 970)
    dim_source = (1130, 330, 1530, 620)
    agg = (1130, 720, 1530, 930)

    draw_box(
        draw,
        fact,
        "dw.fact_energy_generation",
        [
            "PK/FK date_key",
            "PK/FK country_key",
            "PK/FK source_key",
            "electricity_twh",
            "electricity_share_pct",
            "population, gdp",
            "created_at",
            "Grão: país + ano + fonte",
        ],
        "#ffffff",
        "#2a9d8f",
    )
    draw_box(
        draw,
        dim_date,
        "dw.dim_date",
        [
            "PK date_key",
            "year",
            "decade",
            "year_start_date",
            "is_current_year",
            "is_latest_dataset_year",
        ],
        "#ffffff",
        "#3a7ca5",
    )
    draw_box(
        draw,
        dim_country,
        "dw.dim_country (SCD 2)",
        [
            "PK country_key",
            "country_name, iso_code",
            "population_band",
            "gdp_per_capita_band",
            "start_year, end_year",
            "is_current",
        ],
        "#ffffff",
        "#e9b44c",
    )
    draw_box(
        draw,
        dim_source,
        "dw.dim_energy_source",
        [
            "PK source_key",
            "source_code",
            "source_name",
            "source_group",
            "is_renewable",
            "is_low_carbon",
        ],
        "#ffffff",
        "#6a4c93",
    )
    draw_box(
        draw,
        agg,
        "Tabela agregada",
        [
            "dw.fact_energy_generation_annual_grouped",
            "year",
            "country_name",
            "source_group",
            "electricity_twh",
        ],
        "#ffffff",
        "#6c5b4c",
    )

    draw_arrow(draw, (470, 265), (540, 465))
    draw_arrow(draw, (500, 825), (540, 625))
    draw_arrow(draw, (1130, 475), (1060, 515))
    draw_arrow(draw, (1130, 805), (1060, 645), "#6c5b4c")

    draw.text((580, 740), "Relacionamentos por chaves substitutas", font=get_font(20, bold=True), fill="#24313d")
    draw.text((580, 770), "A fato referencia a versão SCD válida do país no ano da observação.", font=get_font(18), fill="#526171")
    image.save(DIAGRAM_PNG)


def main() -> None:
    generate_star_schema_png()
    generate_report_figure_pngs()
    generate_report_pdf()
    print(f"PDF gerado: {REPORT_PDF}")
    print(f"PNG gerado: {DIAGRAM_PNG}")


if __name__ == "__main__":
    main()
