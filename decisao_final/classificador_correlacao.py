"""
Módulo (c) — Classificador de correlação (decisão final)
--------------------------------------------------------------
Lê resultados/semantica_textual/*.json (saída do módulo b) e aplica o
cruzamento lógico descrito na metodologia do projeto: um dark pattern
crítico é identificado quando um sinal ESTRUTURAL (inserção não
requisitada, timer, checkbox pré-marcado, baixa saliência visual) está
CORRELACIONADO com um sinal SEMÂNTICO compatível (cobrança periférica,
urgência artificial, linguagem de retenção) — nunca um dos dois sozinho.

É essa correlação que resolve os hard negatives sem precisar de exceção
manual: um timer com formato mm:ss (estrutural) sem nenhuma palavra de
urgência ao redor (semântico) não é confirmado; um valor monetário
inserido via mutação (estrutural) cujo nome é uma cobrança padrão como
"Frete" (semântico) também não é confirmado, mesmo que estruturalmente
pareça idêntico a uma taxa oculta.

Uso:
    python classificador_correlacao.py
"""

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_ENTRADA = RAIZ / "resultados" / "semantica_textual"
PASTA_SAIDA = RAIZ / "resultados" / "decisao_final"


def decidir_furtividade(elemento: dict) -> dict | None:
    tags = elemento["semantica"]["tagsSemanticas"]
    if "valor_monetario" not in elemento["padroesDetectados"]:
        return None

    pontos = 0
    motivos = []

    if elemento["tipoEvento"] == "insercao_nova":
        pontos += 2
        motivos.append("elemento monetário inserido sem nó anterior correspondente (não requisitado)")
    elif elemento["tipoEvento"] == "substituicao_elemento":
        pontos += 1
        motivos.append("elemento monetário substituiu um placeholder já existente")

    if "cobranca_financeira_periferica" in tags:
        pontos += 2
        motivos.append(f"nome de cobrança compatível com furtividade ({', '.join(elemento['semantica']['evidencias'].get('cobranca_financeira_periferica', []))})")

    if "cobranca_padrao_esperada" in tags:
        # Override: cobrança com nome padrão (frete, imposto...) e
        # nenhum termo suspeito -> não é furtividade, mesmo com mutação.
        return {
            "categoria": "furtividade",
            "darkPatternCritico": False,
            "nivelConfianca": "alta",
            "justificativa": f"valor monetário inserido/substituído, mas com nome de cobrança padrão e esperado ({', '.join(elemento['semantica']['evidencias'].get('cobranca_padrao_esperada', []))}), sem termo de ocultação — correlação descarta furtividade",
        }

    if pontos >= 3:
        return {
            "categoria": "furtividade",
            "darkPatternCritico": True,
            "nivelConfianca": "alta",
            "justificativa": " + ".join(motivos),
        }
    if pontos > 0:
        return {
            "categoria": "furtividade",
            "darkPatternCritico": False,
            "nivelConfianca": "baixa (revisar manualmente — Momento 3)",
            "justificativa": " + ".join(motivos) if motivos else "sinal estrutural fraco, sem confirmação semântica",
        }
    return None


def decidir_acao_forcada(elemento: dict) -> dict | None:
    padroes = elemento["padroesDetectados"]
    tags = elemento["semantica"]["tagsSemanticas"]

    if "checkbox_pre_marcado" in padroes:
        return {
            "categoria": "acao_forcada",
            "darkPatternCritico": True,
            "nivelConfianca": "alta",
            "justificativa": "checkbox de opt-in vem marcado por padrão (fato estrutural inequívoco, não depende de semântica)",
        }

    if "formato_temporal" in padroes:
        if "urgencia_artificial" in tags:
            evid = elemento["semantica"]["evidencias"].get("urgencia_artificial", [])
            return {
                "categoria": "acao_forcada",
                "darkPatternCritico": True,
                "nivelConfianca": "alta",
                "justificativa": f"contador em formato mm:ss correlacionado com linguagem de urgência ({', '.join(evid)})",
            }
        return {
            "categoria": "acao_forcada",
            "darkPatternCritico": False,
            "nivelConfianca": "alta",
            "justificativa": "formato de horário mm:ss presente, mas sem nenhum termo de urgência ao redor — correlação descarta ação forçada (ex.: data/hora real de promoção)",
        }
    return None


def decidir_obstrucao(elemento: dict) -> dict | None:
    padroes = elemento["padroesDetectados"]
    tags = elemento["semantica"]["tagsSemanticas"]
    if "baixa_saliencia_visual" not in padroes:
        return None

    if "linguagem_retencao" in tags:
        evid = elemento["semantica"]["evidencias"].get("linguagem_retencao", [])
        return {
            "categoria": "obstrucao",
            "darkPatternCritico": True,
            "nivelConfianca": "alta",
            "justificativa": f"elemento com baixa saliência visual correlacionado com linguagem de cancelamento/retenção ({', '.join(evid)})",
        }
    return {
        "categoria": "obstrucao",
        "darkPatternCritico": False,
        "nivelConfianca": "baixa (revisar manualmente — Momento 3)",
        "justificativa": "baixa saliência visual detectada, mas sem linguagem de cancelamento/retenção associada — pode ser estilo visual não relacionado a dark pattern",
    }


def decidir(elemento: dict) -> dict:
    candidatos = [
        d for d in (
            decidir_furtividade(elemento),
            decidir_acao_forcada(elemento),
            decidir_obstrucao(elemento),
        ) if d is not None
    ]
    if not candidatos:
        return {
            "categoria": None,
            "darkPatternCritico": False,
            "nivelConfianca": "alta",
            "justificativa": "nenhum sinal estrutural relevante ou nenhuma correlação semântica encontrada",
        }
    # Prioriza confirmações positivas; se houver mais de uma categoria
    # candidata, isso é um caso interessante para o Momento 3 (não deveria
    # ser comum, já que cada padrão estrutural mapeia para no máximo uma
    # regra de correlação nos nossos dados atuais).
    confirmadas = [d for d in candidatos if d["darkPatternCritico"]]
    if confirmadas:
        if len(confirmadas) > 1:
            confirmadas[0]["justificativa"] += " [ATENÇÃO: mais de uma categoria confirmada no mesmo elemento — revisar manualmente]"
        return confirmadas[0]
    return candidatos[0]


def processar_todas_as_paginas() -> None:
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(PASTA_ENTRADA.glob("*.json"))
    print(f"Encontrados {len(arquivos)} JSON(s) semânticos em {PASTA_ENTRADA}\n")

    for arquivo in arquivos:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        pagina = dados["pagina"]
        print(f"=== {pagina} ===")

        for elemento in dados["elementosCaptados"]:
            decisao = decidir(elemento)
            elemento["decisaoFinal"] = decisao
            marcador = "✔ CONFIRMADO" if decisao["darkPatternCritico"] else "—"
            print(f"  [{marcador}] {elemento['idElemento']} ({elemento['tipoEvento']}): "
                  f"{decisao['categoria'] or 'nenhum'} — {decisao['justificativa']}")

        saida = PASTA_SAIDA / arquivo.name
        saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        print()

    print(f"Decisões finais salvas em {PASTA_SAIDA}")


if __name__ == "__main__":
    processar_todas_as_paginas()
