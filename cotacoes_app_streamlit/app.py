import streamlit as st
import pandas as pd

from utils.parser import parse_text, parse_aereos
from utils.pivot import montar_pivot, montar_simulador
from utils.excel_gen import gerar_excel
from utils.pdf_gen import gerar_pdf

st.set_page_config(page_title="Gerador de Cotações", page_icon="🧳", layout="wide")

if "dados" not in st.session_state:
    st.session_state.dados = None
if "aereos" not in st.session_state:
    st.session_state.aereos = []

# ----------------- sidebar -----------------
with st.sidebar:
    st.header("🎨 Identidade visual")
    logo_file = st.file_uploader("Logo (opcional)", type=["png", "jpg", "jpeg"])
    cor_hex = st.color_picker("Cor principal", value="#1F4E78")

    st.divider()
    st.header("👥 Simulador de grupo")
    qtd_apartamentos = st.number_input("Quantidade de apartamentos", min_value=1, value=18, step=1)
    taxa_percentual = st.number_input("Taxa aplicada (%)", min_value=0.0, value=13.0, step=0.5)

st.title("🧳 Gerador de Cotações — Excel & PDF")
st.caption("Cole os textos recebidos do fornecedor e gere os documentos automaticamente.")

# ----------------- entrada: hospedagem -----------------
st.subheader("🏨 Hospedagem")
texto = st.text_area(
    "Cole aqui o texto da cotação de hospedagem",
    height=220,
    placeholder=(
        "Hotel: Windsor Plaza Brasília\n"
        "Até 18 apartamentos singles\n"
        "1º - 20/09 a 26/09/2026 - Confirmação sujeita a disponibilidade\n\n"
        "20/09/2026 - Diária\n"
        "Superior Executivo/Superior Plus single: R$ 830,00 + taxas\n"
        "..."
    ),
)

# ----------------- entrada: aéreos -----------------
st.subheader("✈️ Aéreos (opcional)")
texto_aereos = st.text_area(
    "Cole aqui as informações dos voos, por pessoa e por período",
    height=160,
    placeholder=(
        "Aéreos – IDA E VOLTA - primeiro período:\n"
        "WALID – 2160,00 – GOL\n"
        "MESQUITA – 1104,00 – GOL / 1128,00 - LATAM\n"
        "..."
    ),
)

# ----------------- entrada: condições gerais -----------------
st.subheader("📋 Condições Gerais (opcional)")
condicoes_gerais = st.text_area(
    "Uma condição por linha (vira uma lista bonita no PDF)",
    height=120,
    placeholder=(
        "Café da manhã incluso, servido no restaurante\n"
        "Wi-Fi gratuito em todas as acomodações\n"
        "Taxas: 10% de serviço + 3% de ISS\n"
        "Confirmação sujeita a disponibilidade no momento da reserva"
    ),
)

processar = st.button("🔍 Processar textos", type="primary")

if processar:
    if not texto.strip():
        st.warning("Cole ao menos o texto de hospedagem antes de processar.")
    else:
        st.session_state.dados = parse_text(texto)
        st.session_state.aereos = parse_aereos(texto_aereos) if texto_aereos.strip() else []
        st.success("Textos processados! Revise as tabelas abaixo antes de gerar os arquivos.")

# ----------------- revisão / edição -----------------
if st.session_state.dados:
    dados = st.session_state.dados

    st.divider()
    st.subheader("📋 Revisão — Hospedagem")

    col1, col2 = st.columns(2)
    with col1:
        nome_fornecedor = st.text_input("Fornecedor / Hotel", value=dados.get("nome_fornecedor", ""))
    with col2:
        observacoes_gerais = st.text_input("Observações gerais", value=dados.get("observacoes_gerais", ""))

    itens = dados.get("itens", [])
    df_itens = pd.DataFrame(itens) if itens else pd.DataFrame(
        columns=["periodo", "descricao", "data", "dias", "ocupacao", "valor", "observacao"]
    )
    for col in ["periodo", "descricao", "data", "dias", "ocupacao", "valor", "observacao"]:
        if col not in df_itens.columns:
            df_itens[col] = 1 if col == "dias" else ""
    df_itens = df_itens[["periodo", "descricao", "data", "dias", "ocupacao", "valor", "observacao"]]

    if df_itens.empty:
        st.warning("Nenhum item identificado automaticamente. Adicione as linhas manualmente.")

    st.caption("Edite, adicione ou remova linhas de hospedagem diretamente na tabela:")
    df_itens_editado = st.data_editor(
        df_itens,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "periodo": st.column_config.TextColumn("Período", width="medium"),
            "descricao": st.column_config.TextColumn("Descrição (categoria + ocupação)", width="large"),
            "data": st.column_config.TextColumn("Data"),
            "dias": st.column_config.NumberColumn(
                "Nº dias", help="Quantos dias essa linha representa (ex: '21,22 e 23/09' = 3 dias). Usado no simulador.", min_value=1, step=1
            ),
            "ocupacao": st.column_config.TextColumn("Ocupação"),
            "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            "observacao": st.column_config.TextColumn("Observação"),
        },
        key="editor_itens",
    )

    # ----------------- revisão: aéreos -----------------
    st.subheader("✈️ Revisão — Aéreos")
    df_aereos = pd.DataFrame(st.session_state.aereos) if st.session_state.aereos else pd.DataFrame(
        columns=["periodo", "nome", "cia", "valor"]
    )
    for col in ["periodo", "nome", "cia", "valor"]:
        if col not in df_aereos.columns:
            df_aereos[col] = ""
    df_aereos = df_aereos[["periodo", "nome", "cia", "valor"]]

    st.caption("Edite, adicione ou remova passageiros/valores de aéreos:")
    df_aereos_editado = st.data_editor(
        df_aereos,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "periodo": st.column_config.TextColumn("Período", width="large"),
            "nome": st.column_config.TextColumn("Passageiro"),
            "cia": st.column_config.TextColumn("Companhia"),
            "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
        },
        key="editor_aereos",
    )

    st.divider()
    st.subheader("📥 Gerar documentos")

    itens_finais = df_itens_editado.fillna("").to_dict(orient="records")
    aereos_finais = df_aereos_editado.fillna("").to_dict(orient="records")
    pivot_rows = montar_pivot(itens_finais)
    simulador_rows = montar_simulador(pivot_rows, qtd_apartamentos, taxa_percentual)
    logo_bytes = logo_file.read() if logo_file else None

    col_x, col_y = st.columns(2)
    with col_x:
        excel_buffer = gerar_excel(
            nome_fornecedor, observacoes_gerais, pivot_rows, aereos_finais,
            simulador_rows, qtd_apartamentos, taxa_percentual,
        )
        st.download_button(
            "⬇️ Baixar Excel",
            data=excel_buffer,
            file_name=f"cotacao_{nome_fornecedor.replace(' ', '_') or 'documento'}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_y:
        pdf_buffer = gerar_pdf(
            nome_fornecedor, observacoes_gerais, pivot_rows, aereos_finais,
            condicoes_gerais, simulador_rows, qtd_apartamentos, taxa_percentual,
            logo_bytes, cor_hex,
        )
        st.download_button(
            "⬇️ Baixar PDF",
            data=pdf_buffer,
            file_name=f"cotacao_{nome_fornecedor.replace(' ', '_') or 'documento'}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
