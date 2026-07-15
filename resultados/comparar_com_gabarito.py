"""
Comparação com o gabarito (Etapa 4)
--------------------------------------------------------------
Este script faz duas coisas bem separadas — importante não confundir:

1) AUTOMÁTICO: para toda linha de gabarito/rotulos.csv, procura o
   elemento correspondente em resultados/decisao_final/<id_pagina>.json
   e preenche a coluna `detectado_sistema`. Isso não depende de
   nenhuma rotulagem humana — é só ler o que o pipeline já decidiu.

2) DEPENDENTE DE ROTULAGEM HUMANA: as colunas `tipo_dp_esperado` e
   `detectado_manual` só existem depois do Momento 1 (páginas reais)
   ou do Momento 2 (páginas sintéticas, feito por revisor cego).
   Sem isso preenchido, o script NÃO inventa nada — ele avisa quantas
   linhas ainda faltam e só calcula métricas para o que já tem rótulo.

Saída: resultados/tabela_resultados.csv (sempre gerado, mesmo parcial)
e, se houver dados humanos suficientes, resultados/metricas.json com
Precisão/Recall/F1 (agregado, por categoria, por origem) e o teste de
McNemar comparando manual x automático.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

RAIZ = Path(__file__).resolve().parent.parent
GABARITO_CSV = RAIZ / "gabarito" / "rotulos.csv"
PASTA_DECISAO = RAIZ / "resultados" / "decisao_final"
SAIDA_CSV = RAIZ / "resultados" / "tabela_resultados.csv"
SAIDA_METRICAS = RAIZ / "resultados" / "metricas.json"

MAPA_CATEGORIA_SISTEMA = {
    "furtividade": "Furtividade",
    "acao_forcada": "Ação Forçada",
    "obstrucao": "Obstrução",
    None: "Nenhum",
}


def normalizar_gabarito(valor: str) -> str:
    """'Nenhum (hard negative)', 'Nenhum (hard negative estrutural)' -> 'Nenhum'."""
    valor = (valor or "").strip()
    if valor.startswith("Nenhum"):
        return "Nenhum"
    return valor


def carregar_decisoes() -> dict:
    """id_pagina -> {id_elemento -> categoria_sistema}"""
    decisoes = {}
    for arquivo in PASTA_DECISAO.glob("*.json"):
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        mapa = {}
        for el in dados.get("elementosCaptados", []):
            decisao = el.get("decisaoFinal", {})
            categoria_sistema = decisao.get("categoria") if decisao.get("darkPatternCritico") else None
            mapa[el["idElemento"]] = MAPA_CATEGORIA_SISTEMA.get(categoria_sistema, "Nenhum")
        decisoes[dados["pagina"]] = mapa
    return decisoes


def classificar_resultado(esperado: str, obtido: str) -> str:
    """VP/FP/FN/VN a partir do rótulo esperado (gabarito) x o que foi obtido
    (sistema ou manual). 'Nenhum' é tratado como a classe negativa."""
    esperado_positivo = esperado != "Nenhum"
    obtido_positivo = obtido != "Nenhum"
    if esperado_positivo and obtido_positivo and esperado == obtido:
        return "VP"
    if esperado_positivo and (not obtido_positivo or esperado != obtido):
        return "FN"
    if not esperado_positivo and obtido_positivo:
        return "FP"
    return "VN"


def main():
    if not GABARITO_CSV.exists():
        print(f"AVISO: {GABARITO_CSV} não encontrado. Nada a comparar ainda.")
        return

    decisoes = carregar_decisoes()
    linhas_saida = []
    faltando_rotulagem = []
    elemento_nao_encontrado = []

    with GABARITO_CSV.open(encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            id_pagina = linha["id_pagina"]
            id_elemento = linha["id_elemento"]
            tipo_esperado_bruto = linha["tipo_dp_esperado"]
            detectado_manual_bruto = linha["detectado_manual"]
            origem = linha["origem"]

            pagina_existe = id_pagina in decisoes
            categoria_sistema = decisoes.get(id_pagina, {}).get(id_elemento)
            if categoria_sistema is None:
                if not pagina_existe:
                    # Erro real: a página nem rodou nesta execução do pipeline.
                    elemento_nao_encontrado.append(f"{id_pagina}/{id_elemento} (página ausente em decisao_final/)")
                    categoria_sistema = "(página não encontrada)"
                else:
                    # A página rodou, mas o sensor não achou nada digno de nota
                    # para este elemento específico -> resposta do sistema é
                    # "Nenhum" (correto para hard negatives, ex.: checkbox
                    # opcional que continua desmarcado).
                    categoria_sistema = "Nenhum"

            linha_saida = {
                "id_pagina": id_pagina,
                "id_elemento": id_elemento,
                "tipo_dp_esperado": tipo_esperado_bruto,
                "origem": origem,
                "detectado_manual": detectado_manual_bruto,
                "detectado_sistema": categoria_sistema,
                "resultado_sistema": "",
                "resultado_manual": "",
            }

            if not tipo_esperado_bruto.strip():
                faltando_rotulagem.append(f"{id_pagina}/{id_elemento}")
            else:
                esperado = normalizar_gabarito(tipo_esperado_bruto)
                if categoria_sistema != "(página não encontrada)":
                    linha_saida["resultado_sistema"] = classificar_resultado(esperado, categoria_sistema)
                if detectado_manual_bruto.strip():
                    linha_saida["resultado_manual"] = classificar_resultado(
                        esperado, normalizar_gabarito(detectado_manual_bruto)
                    )

            linhas_saida.append(linha_saida)

    SAIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA_CSV.open("w", encoding="utf-8", newline="") as f:
        campos = ["id_pagina", "id_elemento", "tipo_dp_esperado", "origem",
                  "detectado_manual", "detectado_sistema", "resultado_sistema", "resultado_manual"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas_saida)

    print(f"detectado_sistema preenchido automaticamente para {len(linhas_saida)} linha(s).")
    print(f"Tabela salva em {SAIDA_CSV}\n")

    if elemento_nao_encontrado:
        print("AVISO — elementos do gabarito que o sensor não captou nesta execução "
              "(confira se o id bate com o HTML, ou rode o pipeline de novo):")
        for item in elemento_nao_encontrado:
            print(f"  - {item}")
        print()

    if faltando_rotulagem:
        print(f"PENDENTE (rotulagem humana — Momento 1/2): {len(faltando_rotulagem)} de {len(linhas_saida)} "
              f"linha(s) ainda sem `tipo_dp_esperado` preenchido:")
        for item in faltando_rotulagem:
            print(f"  - {item}")
        print("\nMétricas (Precisão/Recall/F1/McNemar) não calculadas — dependem dessas linhas.")
        return

    calcular_metricas(linhas_saida)


def calcular_metricas(linhas):
    from sklearn.metrics import precision_recall_fscore_support

    linhas_com_manual = [l for l in linhas if l["detectado_manual"].strip()]
    if len(linhas_com_manual) < len(linhas):
        print(f"AVISO: {len(linhas) - len(linhas_com_manual)} linha(s) sem `detectado_manual` — "
              f"a Condição A (manual) e o McNemar só usarão as linhas completas.\n")

    def bloco(nome, subset):
        if not subset:
            return None
        y_esperado = [normalizar_gabarito(l["tipo_dp_esperado"]) for l in subset]
        y_sistema = [l["detectado_sistema"] for l in subset]
        p, r, f1, _ = precision_recall_fscore_support(
            y_esperado, y_sistema, average="macro", zero_division=0
        )
        print(f"[{nome}] n={len(subset)} | Precisão={p:.2f} Recall={r:.2f} F1={f1:.2f}")
        return {"n": len(subset), "precisao": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}

    resultado = {"agregado": bloco("agregado (sistema)", linhas)}

    print("\n--- Por origem (real x sintético) ---")
    for origem in sorted({l["origem"] for l in linhas}):
        resultado[f"origem_{origem}"] = bloco(f"origem={origem}", [l for l in linhas if l["origem"] == origem])

    print("\n--- Por categoria esperada ---")
    for cat in sorted({normalizar_gabarito(l["tipo_dp_esperado"]) for l in linhas}):
        resultado[f"categoria_{cat}"] = bloco(f"categoria={cat}", [l for l in linhas if normalizar_gabarito(l["tipo_dp_esperado"]) == cat])

    if len(linhas_com_manual) >= 4:
        resultado["mcnemar"] = rodar_mcnemar(linhas_com_manual)
    else:
        print("\nMcNemar não calculado: menos de 4 linhas com `detectado_manual` preenchido.")

    SAIDA_METRICAS.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nMétricas salvas em {SAIDA_METRICAS}")


def rodar_mcnemar(linhas):
    from statsmodels.stats.contingency_tables import mcnemar
    import numpy as np

    # Tabela 2x2: manual acertou? (sim/não) x sistema acertou? (sim/não)
    manual_acertou_sistema_acertou = 0
    manual_acertou_sistema_errou = 0
    manual_errou_sistema_acertou = 0
    manual_errou_sistema_errou = 0

    for l in linhas:
        esperado = normalizar_gabarito(l["tipo_dp_esperado"])
        manual_ok = normalizar_gabarito(l["detectado_manual"]) == esperado
        sistema_ok = l["detectado_sistema"] == esperado
        if manual_ok and sistema_ok:
            manual_acertou_sistema_acertou += 1
        elif manual_ok and not sistema_ok:
            manual_acertou_sistema_errou += 1
        elif not manual_ok and sistema_ok:
            manual_errou_sistema_acertou += 1
        else:
            manual_errou_sistema_errou += 1

    tabela = np.array([
        [manual_acertou_sistema_acertou, manual_acertou_sistema_errou],
        [manual_errou_sistema_acertou, manual_errou_sistema_errou],
    ])
    resultado_teste = mcnemar(tabela, exact=True)
    print(f"\nMcNemar: estatística={resultado_teste.statistic:.3f} | p-valor={resultado_teste.pvalue:.4f}")
    return {"tabela_2x2": tabela.tolist(), "estatistica": float(resultado_teste.statistic), "p_valor": float(resultado_teste.pvalue)}


if __name__ == "__main__":
    main()
