"""Gera o PDF de apresentação da cotação: hospedagem (pivotada), aéreos,
condições gerais e simulador de cotação de grupo."""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

COR_PRIMARIA_PADRAO = colors.HexColor("#1F4E78")
COR_CLARA = colors.HexColor("#F2F6FA")
COR_CINZA = colors.HexColor("#F2F2F2")
COR_TEXTO_SEC = colors.HexColor("#555555")
COR_BORDA = colors.HexColor("#D9D9D9")


def _fmt_real(valor) -> str:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_pdf(
    nome_fornecedor: str,
    observacoes_gerais: str,
    pivot_rows: list,
    aereos_rows: list,
    condicoes_gerais: str,
    simulador_rows: list,
    qtd_apartamentos: float,
    taxa_percentual: float,
    logo_bytes: bytes | None = None,
    cor_hex: str | None = None,
) -> io.BytesIO:
    cor_primaria = colors.HexColor(cor_hex) if cor_hex else COR_PRIMARIA_PADRAO

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle("TituloCustom", parent=styles["Heading1"], textColor=cor_primaria, fontSize=19, spaceAfter=2)
    subtitulo_style = ParagraphStyle("SubtituloCustom", parent=styles["Normal"], textColor=colors.grey, fontSize=8.5, spaceAfter=10)
    secao_style = ParagraphStyle("SecaoCustom", parent=styles["Heading2"], textColor=cor_primaria, fontSize=13, spaceBefore=14, spaceAfter=6)
    subsecao_style = ParagraphStyle("SubsecaoCustom", parent=styles["Heading3"], textColor=colors.HexColor("#333333"), fontSize=10.5, spaceBefore=8, spaceAfter=4)
    texto_style = ParagraphStyle("TextoCustom", parent=styles["Normal"], fontSize=9, leading=13, textColor=COR_TEXTO_SEC)
    bullet_style = ParagraphStyle("BulletCustom", parent=styles["Normal"], fontSize=8.7, leading=13, leftIndent=10, textColor=colors.HexColor("#333333"))
    cell_style = ParagraphStyle("CellCustom", parent=styles["Normal"], fontSize=8.5, leading=11)

    elementos = []

    # --- cabeçalho ---
    if logo_bytes:
        try:
            img = Image(io.BytesIO(logo_bytes))
            img._restrictSize(4 * cm, 2.3 * cm)
            elementos.append(img)
            elementos.append(Spacer(1, 0.25 * cm))
        except Exception:
            pass

    elementos.append(Paragraph(f"Cotação — {nome_fornecedor}", titulo_style))
    elementos.append(Paragraph(f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitulo_style))
    elementos.append(HRFlowable(width="100%", color=cor_primaria, thickness=1.2))
    elementos.append(Spacer(1, 0.3 * cm))

    # --- caixas de resumo (qtd apartamentos / taxa / observações) ---
    caixa_data = [
        [
            Paragraph("<b>QTD. APARTAMENTOS</b>", ParagraphStyle("c1", fontSize=7.5, textColor=colors.white)),
            Paragraph("<b>TAXAS APLICADAS</b>", ParagraphStyle("c2", fontSize=7.5, textColor=colors.white)),
        ],
        [
            Paragraph(f"<font size=13><b>{int(qtd_apartamentos)}</b></font>", ParagraphStyle("v1", fontSize=13, textColor=colors.white)),
            Paragraph(f"<font size=13><b>{taxa_percentual:.0f}%</b></font>", ParagraphStyle("v2", fontSize=13, textColor=colors.white)),
        ],
    ]
    caixa = Table(caixa_data, colWidths=[9 * cm, 9 * cm])
    caixa.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), cor_primaria),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("ROUNDEDCORNERS", [4, 4, 4, 4]),
            ]
        )
    )
    elementos.append(caixa)
    elementos.append(Spacer(1, 0.35 * cm))

    if observacoes_gerais:
        elementos.append(Paragraph(f"<b>Observações gerais:</b> {observacoes_gerais}", texto_style))
        elementos.append(Spacer(1, 0.1 * cm))

    # --- HOSPEDAGEM (tabela pivotada por período) ---
    if pivot_rows:
        elementos.append(Paragraph("Hospedagem", secao_style))

        periodos = []
        for row in pivot_rows:
            if row["periodo"] not in periodos:
                periodos.append(row["periodo"])
        if not periodos:
            periodos = [""]

        for periodo in periodos:
            linhas_periodo = [r for r in pivot_rows if r["periodo"] == periodo]
            if not linhas_periodo:
                continue
            bloco = []
            if periodo:
                bloco.append(Paragraph(periodo, subsecao_style))

            cabecalho = ["Data", "Categoria", "Single", "Duplo", "Triplo", "Obs."]
            dados_tabela = [cabecalho]
            for r in linhas_periodo:
                dados_tabela.append(
                    [
                        Paragraph(r["data"], cell_style),
                        Paragraph(r["categoria"], cell_style),
                        _fmt_real(r["single"]) if r["single"] is not None else "—",
                        _fmt_real(r["duplo"]) if r["duplo"] is not None else "—",
                        _fmt_real(r["triplo"]) if r["triplo"] is not None else "—",
                        Paragraph(r.get("observacao", "") or "", cell_style),
                    ]
                )
            tabela = Table(dados_tabela, colWidths=[3.1 * cm, 3.9 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 4.2 * cm], repeatRows=1)
            tabela.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), cor_primaria),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("ALIGN", (2, 0), (4, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_CLARA]),
                        ("GRID", (0, 0), (-1, -1), 0.5, COR_BORDA),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            bloco.append(tabela)
            bloco.append(Spacer(1, 0.25 * cm))
            elementos.append(KeepTogether(bloco))

    # --- AÉREOS ---
    if aereos_rows:
        elementos.append(Paragraph("Aéreos — Ida e Volta", secao_style))

        periodos_aereo = []
        for row in aereos_rows:
            if row["periodo"] not in periodos_aereo:
                periodos_aereo.append(row["periodo"])

        for periodo in periodos_aereo:
            linhas_p = [r for r in aereos_rows if r["periodo"] == periodo]
            bloco = []
            if periodo:
                bloco.append(Paragraph(periodo, subsecao_style))
            cabecalho = ["Passageiro", "Companhia", "Valor"]
            dados_tabela = [cabecalho]
            for r in linhas_p:
                dados_tabela.append([r["nome"], r["cia"], _fmt_real(r["valor"])])
            tabela = Table(dados_tabela, colWidths=[6 * cm, 6 * cm, 6 * cm], repeatRows=1)
            tabela.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), cor_primaria),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_CLARA]),
                        ("GRID", (0, 0), (-1, -1), 0.5, COR_BORDA),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            bloco.append(tabela)
            bloco.append(Spacer(1, 0.25 * cm))
            elementos.append(KeepTogether(bloco))

    # --- SIMULADOR DE COTAÇÃO DE GRUPO ---
    if simulador_rows:
        elementos.append(Paragraph("Simulador de Cotação de Grupo", secao_style))
        elementos.append(
            Paragraph(
                f"Projeção considerando {int(qtd_apartamentos)} apartamento(s) e {taxa_percentual:.0f}% de taxas sobre a diária base.",
                texto_style,
            )
        )
        elementos.append(Spacer(1, 0.15 * cm))

        cabecalho = ["Período", "Categoria", "Ocup.", "Diária média", "Subtotal diárias", f"Taxas ({taxa_percentual:.0f}%)", "Total do grupo"]
        dados_tabela = [cabecalho]
        for s in simulador_rows:
            dados_tabela.append(
                [
                    Paragraph(s["periodo"], cell_style),
                    Paragraph(s["categoria"], cell_style),
                    s["ocupacao"].capitalize(),
                    _fmt_real(s["diaria_media"]),
                    _fmt_real(s["subtotal"]),
                    _fmt_real(s["taxa_valor"]),
                    _fmt_real(s["total"]),
                ]
            )
        tabela = Table(
            dados_tabela,
            colWidths=[3.6 * cm, 3.6 * cm, 1.8 * cm, 2.6 * cm, 2.8 * cm, 2.6 * cm, 2.8 * cm],
            repeatRows=1,
        )
        tabela.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), cor_primaria),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (-1, 1), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_CLARA]),
                    ("TEXTCOLOR", (-1, 1), (-1, -1), cor_primaria),
                    ("GRID", (0, 0), (-1, -1), 0.5, COR_BORDA),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elementos.append(tabela)
        elementos.append(Spacer(1, 0.3 * cm))

    # --- CONDIÇÕES GERAIS ---
    if condicoes_gerais and condicoes_gerais.strip():
        elementos.append(Paragraph("Condições Gerais & Políticas", secao_style))
        linhas_cond = [l.strip(" -•") for l in condicoes_gerais.split("\n") if l.strip()]
        itens_bullet = []
        for linha in linhas_cond:
            itens_bullet.append(Paragraph(f"•  {linha}", bullet_style))
            itens_bullet.append(Spacer(1, 0.08 * cm))

        caixa_cond = Table([[c] for c in itens_bullet], colWidths=[18 * cm])
        caixa_cond.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COR_CINZA),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("BOX", (0, 0), (-1, -1), 0.5, COR_BORDA),
                ]
            )
        )
        elementos.append(caixa_cond)
        elementos.append(Spacer(1, 0.3 * cm))

    # --- rodapé ---
    elementos.append(HRFlowable(width="100%", color=COR_BORDA, thickness=0.5))
    elementos.append(Spacer(1, 0.15 * cm))
    elementos.append(
        Paragraph(
            "Valores sujeitos a alteração e disponibilidade no momento da confirmação.",
            ParagraphStyle("Rodape", parent=styles["Normal"], fontSize=7.5, textColor=colors.grey),
        )
    )

    doc.build(elementos)
    buffer.seek(0)
    return buffer
