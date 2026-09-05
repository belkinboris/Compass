# -*- coding: utf-8 -*-
"""Брендированный PDF карточки сделки для платного тарифа."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from xml.sax.saxutils import escape


# Шрифт с кириллицей едет В ПОСТАВКЕ (static/fonts/DejaVuSans*.ttf, лицензия
# DejaVu/Bitstream Vera — свободная), а системные каталоги — только запасной
# путь. До 5 сентября 2026 искали только в /usr/share/fonts: в среде
# разработки они есть, на боевом хосте — нет, и PDF уходил читателю на
# Helvetica без кириллицы — квадраты вместо русского текста (аудит перед
# бетой). Проверять надо файл из того же окружения, где работает сайт.
FONT_DIR = Path(__file__).resolve().parent / "static" / "fonts"


def _font_path(*names: str) -> str | None:
    roots = [FONT_DIR, Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/truetype/liberation2")]
    for root in roots:
        for name in names:
            path = root / name
            if path.exists():
                return str(path)
    return None


def _register_fonts() -> tuple[str, str]:
    regular = _font_path("DejaVuSans.ttf", "LiberationSans-Regular.ttf")
    bold = _font_path("DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf")
    if regular:
        pdfmetrics.registerFont(TTFont("CompassSans", regular))
    if bold:
        pdfmetrics.registerFont(TTFont("CompassSansBold", bold))
    return ("CompassSans" if regular else "Helvetica", "CompassSansBold" if bold else "Helvetica-Bold")


def _text(value: Any) -> str:
    if value is None or value == "":
        return "Не раскрыто"
    return str(value)


def render_deal_pdf(deal: dict[str, Any]) -> bytes:
    regular, bold = _register_fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm,
                            title=_text(deal.get("title")), author="КОМПАС")
    styles = getSampleStyleSheet()
    brand = colors.HexColor("#0F2B21")
    bronze = colors.HexColor("#A3814E")
    muted = colors.HexColor("#66707A")
    title = ParagraphStyle("CompassTitle", parent=styles["Title"], fontName=bold,
                           fontSize=22, leading=27, textColor=colors.HexColor("#15191D"), alignment=TA_LEFT)
    h2 = ParagraphStyle("CompassH2", parent=styles["Heading2"], fontName=bold,
                        fontSize=11, leading=15, textColor=brand, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("CompassBody", parent=styles["BodyText"], fontName=regular,
                          fontSize=9.5, leading=14, textColor=colors.HexColor("#30363B"))
    small = ParagraphStyle("CompassSmall", parent=body, fontSize=8, leading=11, textColor=muted)

    story: list[Any] = []
    story.append(Paragraph("КОМПАС", ParagraphStyle("Brand", parent=body, fontName=bold,
                                                     fontSize=16, textColor=brand, spaceAfter=12)))
    story.append(Paragraph(escape(_text(deal.get("title"))), title))
    meta = " · ".join(x for x in (_text(deal.get("date")), _text(deal.get("status")),
                                  _text(deal.get("type")), _text(deal.get("ind"))) if x and x != "Не раскрыто")
    story.append(Spacer(1, 5*mm)); story.append(Paragraph(escape(meta), small)); story.append(Spacer(1, 5*mm))

    facts = [
        ["Покупатель", _text(deal.get("buyer_name") or deal.get("buyer_label"))],
        ["Продавец", _text(deal.get("seller") or deal.get("seller_name"))],
        ["Объект сделки", _text(deal.get("asset") or deal.get("target_name"))],
        ["Сумма", _text(deal.get("sum"))],
    ]
    tbl = Table([[Paragraph(f"<b>{escape(k)}</b>", small), Paragraph(escape(v), body)] for k,v in facts], colWidths=[42*mm, 118*mm])
    tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),("LINEBELOW",(0,0),(-1,-1),0.35,colors.HexColor("#E2E5DF")),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    story.append(tbl)

    def add_section(label: str, values: list[tuple[str, Any]]) -> None:
        present = [(k,v) for k,v in values if v not in (None,"","—")]
        if not present:
            return
        story.append(Paragraph(label, h2))
        for key, value in present:
            story.append(Paragraph(f"<b>{escape(key)}.</b> {escape(_text(value))}", body))
            story.append(Spacer(1, 2*mm))

    eco = deal.get("eco") if isinstance(deal.get("eco"), dict) else {}
    law = deal.get("law") if isinstance(deal.get("law"), dict) else {}
    add_section("ЭКОНОМИЧЕСКИЙ ОБЗОР", [
        ("Сумма", eco.get("sum")), ("Доля и периметр", eco.get("share")),
        ("Оценка", eco.get("val")), ("Показатели объекта", eco.get("target_fin")),
        ("Финансирование", eco.get("fin")), ("Мотивы", eco.get("rationale")),
        ("Контекст", eco.get("context")),
    ])
    add_section("ЮРИДИЧЕСКИЙ ОБЗОР", [
        ("Структура", law.get("struct")), ("Согласования", law.get("appr")),
        ("Условия", law.get("terms")),
    ])
    advisors = law.get("adv") if isinstance(law.get("adv"), list) else []
    if advisors:
        story.append(Paragraph("КОМАНДА СДЕЛКИ", h2))
        for item in advisors:
            if isinstance(item, list):
                story.append(Paragraph(" — ".join(escape(_text(x)) for x in item if x), body))
                story.append(Spacer(1, 2*mm))

    sources = deal.get("src") if isinstance(deal.get("src"), list) else []
    if sources:
        story.append(Paragraph("ИСТОЧНИКИ", h2))
        for source in sources:
            if isinstance(source, list) and len(source) >= 2:
                story.append(Paragraph(f'{escape(_text(source[0]))}: <link href="{escape(_text(source[1]))}" color="#1D5A44">{escape(_text(source[1]))}</link>', small))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("Сведения собраны из публичных источников и могут быть неполными. Дата формирования отчёта указывается в свойствах файла.", small))

    def footer(canvas, _doc):
        canvas.saveState(); canvas.setStrokeColor(bronze); canvas.setLineWidth(0.7)
        canvas.line(18*mm, 12*mm, 192*mm, 12*mm)
        canvas.setFont(regular, 7); canvas.setFillColor(muted)
        canvas.drawString(18*mm, 7.5*mm, "projectcompass.ru")
        canvas.drawRightString(192*mm, 7.5*mm, f"стр. {_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
