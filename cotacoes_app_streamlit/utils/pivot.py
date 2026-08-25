"""Monta a tabela pivotada (Data x Ocupação) e o resumo do simulador de grupo,
a partir da lista plana de itens extraída pelo parser."""

import re

OCUPACOES_ORDEM = ["single", "duplo", "triplo", "quádruplo"]


def _remover_ocupacao_da_descricao(descricao: str, ocupacao: str) -> str:
    if not ocupacao:
        return descricao
    return re.sub(re.escape(ocupacao), "", descricao, flags=re.IGNORECASE).strip(" /-")


def montar_pivot(itens: list) -> list:
    """
    Agrupa itens por (período, data, categoria) e organiza os valores de
    single/duplo/triplo em colunas — igual à tabela do modelo de referência.
    """
    grupos = {}
    ordem = []

    for item in itens:
        ocupacao = (item.get("ocupacao") or "").lower()
        categoria = _remover_ocupacao_da_descricao(item.get("descricao", ""), ocupacao) or item.get(
            "descricao", ""
        )
        chave = (item.get("periodo", ""), item.get("data", ""), categoria)

        if chave not in grupos:
            grupos[chave] = {
                "periodo": item.get("periodo", ""),
                "data": item.get("data", ""),
                "dias": item.get("dias", 1),
                "categoria": categoria,
                "single": None,
                "duplo": None,
                "triplo": None,
                "quádruplo": None,
                "observacao": item.get("observacao", ""),
            }
            ordem.append(chave)

        if ocupacao in ("single", "duplo", "triplo", "quádruplo", "quadruplo"):
            col = "quádruplo" if ocupacao == "quadruplo" else ocupacao
            grupos[chave][col] = item.get("valor", 0)
        if item.get("observacao") and not grupos[chave]["observacao"]:
            grupos[chave]["observacao"] = item.get("observacao")

    return [grupos[chave] for chave in ordem]


def montar_simulador(pivot_rows: list, qtd_apartamentos: float, taxa_percentual: float) -> list:
    """
    Para cada (período, categoria, ocupação), soma as diárias de todas as datas —
    ponderando pelo número de dias que cada linha representa (ex: "21,22 e 23/09"
    conta como 3 dias, não como 1) — e projeta o total do grupo.
    """
    grupos = {}
    ordem = []

    for row in pivot_rows:
        dias_linha = row.get("dias", 1) or 1
        for oc in OCUPACOES_ORDEM:
            valor = row.get(oc)
            if valor is None:
                continue
            chave = (row["periodo"], row["categoria"], oc)
            if chave not in grupos:
                grupos[chave] = {
                    "periodo": row["periodo"],
                    "categoria": row["categoria"],
                    "ocupacao": oc,
                    "soma_ponderada": 0.0,
                    "total_dias": 0,
                }
                ordem.append(chave)
            grupos[chave]["soma_ponderada"] += valor * dias_linha
            grupos[chave]["total_dias"] += dias_linha

    resultado = []
    for chave in ordem:
        g = grupos[chave]
        n_dias = g["total_dias"]
        soma = g["soma_ponderada"]
        diaria_media = soma / n_dias if n_dias else 0
        subtotal = soma * qtd_apartamentos
        taxa_valor = subtotal * (taxa_percentual / 100)
        total = subtotal + taxa_valor
        resultado.append(
            {
                "periodo": g["periodo"],
                "categoria": g["categoria"],
                "ocupacao": g["ocupacao"],
                "n_dias": n_dias,
                "diaria_media": diaria_media,
                "subtotal": subtotal,
                "taxa_valor": taxa_valor,
                "total": total,
            }
        )
    return resultado
