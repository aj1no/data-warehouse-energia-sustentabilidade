"""
Projeto: Data Warehouse de Energia e Sustentabilidade
Autores: Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar
Entrega: 03/06/2026

Gera artefatos finais de entrega pelo GitHub, com arquivos normalizados:
- docs/relatorio_tecnico.pdf
- docs/diagrama_modelo_estrela.png
"""

from __future__ import annotations

import re
import sys
from html import escape
from pathlib import Path

LOCAL_DEPS_DIR = Path(__file__).resolve().parents[1] / ".deps"
if LOCAL_DEPS_DIR.exists():
    sys.path.insert(0, str(LOCAL_DEPS_DIR))

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs"
REPORT_MD = DOCS_DIR / "relatorio_tecnico.md"
REPORT_PDF = DOCS_DIR / "relatorio_tecnico.pdf"
DIAGRAM_PNG = DOCS_DIR / "diagrama_modelo_estrela.png"


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


def generate_report_pdf() -> None:
    styles = getSampleStyleSheet()
    styles["Title"].fontSize = 18
    styles["Title"].leading = 22
    styles["Heading2"].fontSize = 13
    styles["Heading2"].leading = 16
    styles["Heading2"].spaceBefore = 12
    styles["Heading2"].spaceAfter = 6
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 12
    styles.add(ParagraphStyle(name="TableCell", parent=styles["BodyText"], fontSize=7, leading=9))

    story = []
    lines = REPORT_MD.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            story.append(Spacer(1, 0.12 * cm))
            i += 1
            continue

        if line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            story.append(markdown_table_to_reportlab(table_lines, styles))
            story.append(Spacer(1, 0.15 * cm))
            continue

        if line.strip().startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                text = lines[i].strip()[2:]
                items.append(ListItem(Paragraph(clean_inline_markdown(text), styles["BodyText"])))
                i += 1
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=16))
            story.append(Spacer(1, 0.1 * cm))
            continue

        if line.strip().startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            code_text = "<br/>".join(line.replace(" ", "&nbsp;") for line in code_lines)
            story.append(Paragraph(f"<font name='Courier'>{code_text}</font>", styles["BodyText"]))
            story.append(Spacer(1, 0.1 * cm))
            continue

        story.append(paragraph_from_markdown(line, styles))
        i += 1

    doc = SimpleDocTemplate(
        str(REPORT_PDF),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title="Relatório Técnico - Data Warehouse de Energia e Sustentabilidade",
        author="Rodolfo Vinicius Cima Takemoto; Tiago Galhardo Avelar",
    )
    doc.build(story)


def get_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


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
        ["PK date_key", "year", "decade", "year_start_date"],
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
    generate_report_pdf()
    generate_star_schema_png()
    print(f"PDF gerado: {REPORT_PDF}")
    print(f"PNG gerado: {DIAGRAM_PNG}")


if __name__ == "__main__":
    main()
