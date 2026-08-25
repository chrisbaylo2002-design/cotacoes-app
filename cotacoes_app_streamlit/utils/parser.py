"""
Extração por regras (regex, sem IA/API) dos dois tipos de texto que o usuário cola:
1) Cotação de hospedagem (hotel/passeio) -> extract_data_fallback / parse_text
2) Cotação de aéreos (por pessoa, por período) -> parse_aereos
"""

import re

PADRAO_PRECO = re.compile(r"^(.+?):\s*R\$\s*([\d\.]+,\d{2})\s*(.*)$")
PADRAO_DATA = re.compile(r"\d{1,2}/\d{2}/\d{4}")
PADRAO_LINHA_DIARIA = re.compile(r"di[aá]ria", re.IGNORECASE)
PADRAO_PERIODO = re.compile(r"^\d+[ºo°]")
NUM_PATTERN = re.compile(r"\d[\d.,]*\d|\d")

OCUPACOES = ["single", "duplo", "triplo", "quádruplo", "quadruplo"]


def contar_dias(data_str: str) -> int:
    """
    Conta quantos dias uma linha de data representa. Ex:
    '20/09/2026' -> 1
    '21,22 e 23/09/2026' -> 3
    '06 e 07/10/2026' -> 2
    """
    m = re.match(r"^\s*(\d{1,2}(?:\s*,\s*\d{1,2}|\s+e\s+\d{1,2})*)\s*/\d{2}/\d{4}", data_str)
    if m:
        dias = re.split(r"\s*,\s*|\s+e\s+", m.group(1).strip())
        dias = [d for d in dias if d.strip()]
        if dias:
            return len(dias)
    # fallback: conta quantas datas completas dd/mm/aaaa aparecem na linha
    datas_completas = PADRAO_DATA.findall(data_str)
    return max(1, len(datas_completas))


def parse_valor_pt(valor_str: str) -> float:
    """Converte um número em formato PT-BR ('1.193,00', '2. 200,00') para float."""
    limpo = re.sub(r"[^\d.,]", "", valor_str)
    if not limpo:
        return 0.0
    if "," in limpo:
        inteiro, decimal = limpo.rsplit(",", 1)
        inteiro = inteiro.replace(".", "").replace(",", "")
        try:
            return float(f"{inteiro}.{decimal}")
        except ValueError:
            return 0.0
    limpo = limpo.replace(".", "")
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def _detectar_ocupacao(descricao: str) -> str:
    desc_lower = descricao.lower()
    for oc in OCUPACOES:
        if oc in desc_lower:
            return oc
    return ""


def extract_data_fallback(text: str) -> dict:
    """Extrai fornecedor, observações gerais e itens (com período) de um texto de hospedagem."""
    linhas = [l.strip() for l in text.split("\n") if l.strip()]

    nome_fornecedor = ""
    observacoes = []
    itens = []
    data_atual = ""
    periodo_atual = ""

    for linha in linhas:
        m_nome = re.match(r"^(hotel|servi[çc]o|passeio|fornecedor)\s*:\s*(.+)$", linha, re.IGNORECASE)
        if m_nome and not nome_fornecedor:
            nome_fornecedor = m_nome.group(2).strip()
            continue

        if PADRAO_PERIODO.match(linha):
            periodo_atual = linha
            observacoes.append(linha)
            continue

        m_preco = PADRAO_PRECO.match(linha)
        if m_preco:
            descricao = m_preco.group(1).strip()
            valor = parse_valor_pt(m_preco.group(2))
            resto = m_preco.group(3).strip()
            itens.append(
                {
                    "periodo": periodo_atual,
                    "descricao": descricao,
                    "data": data_atual,
                    "dias": contar_dias(data_atual) if data_atual else 1,
                    "ocupacao": _detectar_ocupacao(descricao),
                    "valor": valor,
                    "observacao": resto,
                }
            )
            continue

        if PADRAO_LINHA_DIARIA.search(linha) and PADRAO_DATA.search(linha):
            data_atual = linha
            continue

        if PADRAO_DATA.search(linha):
            observacoes.append(linha)
            continue

        if not nome_fornecedor:
            nome_fornecedor = linha
        else:
            observacoes.append(linha)

    return {
        "nome_fornecedor": nome_fornecedor or "Fornecedor não identificado",
        "observacoes_gerais": " | ".join(observacoes),
        "itens": itens,
    }


def parse_text(text: str) -> dict:
    return extract_data_fallback(text)


def _split_valor_cia(opcao: str):
    # remove espaços que estão dentro de um número (ex: "2. 200,00" -> "2.200,00"),
    # sem mexer em espaços entre palavras (ex: "GOL E LATAM")
    opcao = re.sub(r"(?<=[\d.,])\s+(?=[\d.,])", "", opcao)
    m = NUM_PATTERN.search(opcao)
    if not m:
        return 0.0, opcao.strip(" -–")
    valor = parse_valor_pt(m.group(0))
    resto = (opcao[: m.start()] + opcao[m.end() :]).strip(" -–")
    return valor, resto


def parse_aereos(text: str) -> list:
    """
    Extrai passagens aéreas de um texto no formato:

        Aéreos – IDA E VOLTA - primeiro período:
        WALID – 2160,00 – GOL
        MESQUITA – 1104,00 – GOL / 1128,00 - LATAM

        Aéreos – IDA E VOLTA - segundo período:
        WALID – 2040,00 – GOL
        ...

    Cada pessoa pode ter mais de uma opção de companhia (separadas por "/").
    """
    linhas = [l.strip() for l in text.split("\n") if l.strip()]
    resultado = []
    periodo_atual = ""

    for linha in linhas:
        if re.search(r"a[eé]reos", linha, re.IGNORECASE):
            periodo_atual = linha.rstrip(":").strip()
            continue

        idx_candidatos = [i for i in (linha.find("–"), linha.find("-")) if i != -1]
        if not idx_candidatos:
            continue
        idx_dash = min(idx_candidatos)

        nome = linha[:idx_dash].strip()
        resto = linha[idx_dash + 1 :].strip()
        if not nome or not resto:
            continue

        opcoes = [o.strip() for o in resto.split("/") if o.strip()]
        for op in opcoes:
            valor, cia = _split_valor_cia(op)
            resultado.append(
                {"periodo": periodo_atual, "nome": nome.upper(), "cia": cia, "valor": valor}
            )

    return resultado
