"""
Etapa 5 — Gráfico e tabela finais para o artigo
--------------------------------------------------------------
Lê resultados/metricas.json (gerado por comparar_com_gabarito.py) e produz:
  - material-artigo/grafico_comparativo.png (Precisão/Recall/F1, Manual x
    Sistema, nas 3 situações: só real, só sintético, agregado)
  - material-artigo/tabela_comparativa.md (mesmo formato do exemplo do
    Implementacao_Trabalho3.md, com valores REAIS, não fictícios)

Uso:
    python gerar_grafico.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parent.parent
METRICAS_JSON = RAIZ / "resultados" / "metricas.json"
SAIDA_GRAFICO = RAIZ / "material-artigo" / "grafico_comparativo.png"
SAIDA_TABELA = RAIZ / "material-artigo" / "tabela_comparativa.md"

SITUACOES = [
    ("Situação 1 — Só dados reais", "manual_origem_real", "sistema_origem_real", "mcnemar_real"),
    ("Situação 2 — Só dados sintéticos", "manual_origem_sintetica", "sistema_origem_sintetica", "mcnemar_sintetica"),
    ("Situação 3 — Agregado (real + sintético)", "manual_agregado", "sistema_agregado", "mcnemar_agregado"),
]


def carregar_metricas() -> dict:
    if not METRICAS_JSON.exists():
        raise SystemExit(
            f"{METRICAS_JSON} não encontrado. Rode primeiro pipeline/comparar_com_gabarito.py "
            f"com o gabarito completamente rotulado."
        )
    return json.loads(METRICAS_JSON.read_text(encoding="utf-8"))


def gerar_grafico(metricas: dict):
    fig, eixos = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    indicadores = ["precisao", "recall", "f1"]
    rotulos_indicadores = ["Precisão", "Recall", "F1-Score"]
    largura = 0.35

    for eixo, (titulo, chave_manual, chave_sistema, _) in zip(eixos, SITUACOES):
        bloco_manual = metricas.get(chave_manual)
        bloco_sistema = metricas.get(chave_sistema)

        x = range(len(indicadores))
        valores_manual = [bloco_manual[i] if bloco_manual else 0 for i in indicadores]
        valores_sistema = [bloco_sistema[i] if bloco_sistema else 0 for i in indicadores]

        eixo.bar([i - largura / 2 for i in x], valores_manual, largura, label="Condição A (Manual)", color="#5b8def")
        eixo.bar([i + largura / 2 for i in x], valores_sistema, largura, label="Condição B (Automático)", color="#2e7d32")

        eixo.set_xticks(list(x))
        eixo.set_xticklabels(rotulos_indicadores)
        eixo.set_ylim(0, 1.05)
        n_manual = bloco_manual["n"] if bloco_manual else 0
        n_sistema = bloco_sistema["n"] if bloco_sistema else 0
        eixo.set_title(f"{titulo}\n(n manual={n_manual}, n sistema={n_sistema})", fontsize=10)
        for i, v in enumerate(valores_manual):
            eixo.text(i - largura / 2, v + 0.02, f"{v:.2f}", ha="center", fontsize=8)
        for i, v in enumerate(valores_sistema):
            eixo.text(i + largura / 2, v + 0.02, f"{v:.2f}", ha="center", fontsize=8)

    eixos[0].set_ylabel("Valor da métrica")
    eixos[-1].legend(loc="lower right", fontsize=9)
    fig.suptitle("Detecção de Dark Patterns — Manual x Automático, por origem dos dados", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.94])

    SAIDA_GRAFICO.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SAIDA_GRAFICO, dpi=150)
    print(f"Gráfico salvo em {SAIDA_GRAFICO}")


def gerar_tabela_markdown(metricas: dict):
    linhas = ["# Tabela comparativa — valores reais do protótipo\n"]
    for titulo, chave_manual, chave_sistema, chave_mcnemar in SITUACOES:
        bloco_manual = metricas.get(chave_manual)
        bloco_sistema = metricas.get(chave_sistema)
        linhas.append(f"## {titulo}\n")

        if not bloco_manual and not bloco_sistema:
            linhas.append("_Sem dados suficientes para esta situação._\n")
            continue

        linhas.append("| Indicador | Condição A (Manual) | Condição B (Automático) |")
        linhas.append("|---|---|---|")
        for chave, rotulo in [("precisao", "Precisão"), ("recall", "Recall"), ("f1", "F1-Score")]:
            v_manual = f"{bloco_manual[chave]:.2f}" if bloco_manual else "—"
            v_sistema = f"{bloco_sistema[chave]:.2f}" if bloco_sistema else "—"
            linhas.append(f"| {rotulo} | {v_manual} | {v_sistema} |")
        linhas.append(f"\n_n manual={bloco_manual['n'] if bloco_manual else 0}, "
                       f"n sistema={bloco_sistema['n'] if bloco_sistema else 0}_\n")

        mcnemar = metricas.get(chave_mcnemar)
        if mcnemar:
            p = mcnemar["p_valor"]
            veredito = "diferença estatisticamente significativa" if p < 0.05 else "sem diferença estatisticamente significativa"
            linhas.append(f"McNemar ({titulo.split(' — ')[0].lower()}): estatística={mcnemar['estatistica']:.3f}, "
                           f"p={p:.4f} → {veredito}\n")
        else:
            linhas.append("McNemar: não calculado (dados insuficientes nesta situação — menos de 4 pares manual x sistema)\n")

    linhas.append("---\n")
    linhas.append(
        "**Leitura obrigatória (Ameaças à Validade — validade de construção):** "
        "as métricas da Situação 2 e 3 incluem dados sintéticos, que compartilham "
        "template com o que calibrou as heurísticas do detector — há risco de "
        "circularidade residual mesmo com a Regra R2 (vocabulário parcialmente "
        "distinto). Reportar as 3 situações separadamente, como acima, é o que "
        "permite ao leitor avaliar se a conclusão se sustenta nos dados reais "
        "isoladamente (Situação 1), não só no agregado."
    )

    SAIDA_TABELA.write_text("\n".join(linhas), encoding="utf-8")
    print(f"Tabela salva em {SAIDA_TABELA}")


def main():
    metricas = carregar_metricas()
    gerar_grafico(metricas)
    gerar_tabela_markdown(metricas)


if __name__ == "__main__":
    main()
