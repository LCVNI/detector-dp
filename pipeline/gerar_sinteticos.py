"""
Gerador de páginas sintéticas (Etapa 1.5)
--------------------------------------------------------------
Lê os templates parametrizados de paginas/templates/*.html + o manifesto
de variação (manifesto_sintetico.json), combina os slots com random.seed(42)
fixa (Regra R6 — reprodutibilidade), grava as páginas geradas em
paginas/sinteticas/, registra a combinação exata de cada arquivo em
resultados/log_geracao.csv (R6), e já escreve as linhas correspondentes
em gabarito/rotulos.csv com origem='sintetica' — SEM intervenção humana,
porque aqui o rótulo nasce do próprio manifesto (diferente das páginas
reais, onde o rótulo só pode vir de rotulagem cega — Momento 1).

Uso:
    python gerar_sinteticos.py
"""

import csv
import json
import random
from pathlib import Path

SEED = 42
N_INSTANCIAS_POR_NIVEL = 6  # Regra R5 — balanceamento entre categorias

RAIZ = Path(__file__).resolve().parent.parent
PASTA_TEMPLATES = RAIZ / "paginas" / "templates"
PASTA_SAIDA_PAGINAS = RAIZ / "paginas" / "sinteticas"
GABARITO_CSV = RAIZ / "gabarito" / "rotulos.csv"
LOG_GERACAO_CSV = RAIZ / "resultados" / "log_geracao.csv"


def rng_para(categoria: str, nivel: str) -> random.Random:
    """RNG independente por (categoria, nível), derivada da seed global.
    Isso garante que aumentar N_INSTANCIAS_POR_NIVEL numa categoria nunca
    desloca a sequência de sorteios de outra categoria/nível — cada uma
    tem sua própria trilha de números aleatórios, sempre reproduzível
    (Regra R6) e estável entre execuções, mesmo que o volume mude."""
    return random.Random(f"{SEED}-{categoria}-{nivel}")


def carregar_manifesto() -> dict:
    return json.loads((PASTA_TEMPLATES / "manifesto_sintetico.json").read_text(encoding="utf-8"))


def preencher_template(nome_template: str, valores: dict) -> str:
    texto = (PASTA_TEMPLATES / nome_template).read_text(encoding="utf-8")
    for chave, valor in valores.items():
        texto = texto.replace("{{" + chave + "}}", str(valor))
    return texto


def gerar_furtividade(manifesto: dict, log: list, gabarito: list):
    for nivel in ("obvio", "sutil"):
        rng = rng_para("furtividade", nivel)
        dados_nivel = manifesto["furtividade"][nivel]
        for i in range(N_INSTANCIAS_POR_NIVEL):
            tempo = rng.choice(dados_nivel["tempo_mutacao_ms"])
            opcao_taxa = rng.choice(dados_nivel["opcoes_taxa"])
            nome_arquivo = f"furtividade_{nivel}_{i+1:02d}"

            html = preencher_template("furtividade_template.html", {
                "TEMPO_MUTACAO_MS": tempo,
                "TEXTO_TAXA": opcao_taxa["texto"],
                "VALOR_TAXA": f"{opcao_taxa['valor']:.2f}".replace(".", ","),
                "VALOR_TAXA_NUM": opcao_taxa["valor"],
            })
            caminho_pagina = PASTA_SAIDA_PAGINAS / f"{nome_arquivo}.html"
            if caminho_pagina.exists():
                continue  # protege página já gerada (pode já ter sido revisada no Momento 2)
            caminho_pagina.write_text(html, encoding="utf-8")

            log.append({
                "arquivo": nome_arquivo, "categoria": "furtividade", "nivel": nivel,
                "eh_hard_negative": "nao",
                "parametros": json.dumps({"tempo_mutacao_ms": tempo, "opcao_taxa": opcao_taxa}, ensure_ascii=False),
            })
            gabarito.append({
                "id_pagina": nome_arquivo, "id_elemento": "elemento-taxa-oculta",
                "tipo_dp_esperado": "Furtividade", "origem": "sintetica",
                "detectado_manual": "", "detectado_sistema": "", "resultado_sistema": "", "resultado_manual": "",
            })


def gerar_acao_forcada(manifesto: dict, log: list, gabarito: list):
    for nivel in ("obvio", "sutil"):
        rng = rng_para("acao_forcada", nivel)
        dados_nivel = manifesto["acao_forcada"][nivel]
        for i in range(N_INSTANCIAS_POR_NIVEL):
            tempo_inicial = rng.choice(dados_nivel["tempo_inicial_timer"])
            opcao_urgencia = rng.choice(dados_nivel["opcoes_urgencia"])
            nome_arquivo = f"acaoforcada_{nivel}_{i+1:02d}"

            html = preencher_template("acaoforcada_template.html", {
                "TEMPO_INICIAL_TIMER": tempo_inicial,
                "URGENCIA_PREFIXO": opcao_urgencia["prefixo"],
                "URGENCIA_SUFIXO": opcao_urgencia["sufixo"],
            })
            caminho_pagina = PASTA_SAIDA_PAGINAS / f"{nome_arquivo}.html"
            if caminho_pagina.exists():
                continue  # protege página já gerada (pode já ter sido revisada no Momento 2)
            caminho_pagina.write_text(html, encoding="utf-8")

            log.append({
                "arquivo": nome_arquivo, "categoria": "acao_forcada", "nivel": nivel,
                "eh_hard_negative": "nao",
                "parametros": json.dumps({"tempo_inicial_timer": tempo_inicial, "opcao_urgencia": opcao_urgencia}, ensure_ascii=False),
            })
            # Dois elementos suspeitos por instância: o timer e o checkbox.
            gabarito.append({
                "id_pagina": nome_arquivo, "id_elemento": "contador",
                "tipo_dp_esperado": "Ação Forçada", "origem": "sintetica",
                "detectado_manual": "", "detectado_sistema": "", "resultado_sistema": "", "resultado_manual": "",
            })
            gabarito.append({
                "id_pagina": nome_arquivo, "id_elemento": "elemento-checkbox-preselecionado",
                "tipo_dp_esperado": "Ação Forçada", "origem": "sintetica",
                "detectado_manual": "", "detectado_sistema": "", "resultado_sistema": "", "resultado_manual": "",
            })


def gerar_obstrucao(manifesto: dict, log: list, gabarito: list):
    for nivel in ("obvio", "sutil"):
        rng = rng_para("obstrucao", nivel)
        dados_nivel = manifesto["obstrucao"][nivel]
        for i in range(N_INSTANCIAS_POR_NIVEL):
            opcao_retencao = rng.choice(dados_nivel["opcoes_retencao"])
            nome_arquivo = f"obstrucao_{nivel}_{i+1:02d}"

            html = preencher_template("obstrucao_template.html", {
                "TEXTO_RETENCAO_1": opcao_retencao["texto1"],
                "TEXTO_RETENCAO_2": opcao_retencao["texto2"],
            })
            caminho_pagina = PASTA_SAIDA_PAGINAS / f"{nome_arquivo}.html"
            if caminho_pagina.exists():
                continue  # protege página já gerada (pode já ter sido revisada no Momento 2)
            caminho_pagina.write_text(html, encoding="utf-8")

            log.append({
                "arquivo": nome_arquivo, "categoria": "obstrucao", "nivel": nivel,
                "eh_hard_negative": "nao",
                "parametros": json.dumps({"opcao_retencao": opcao_retencao}, ensure_ascii=False),
            })
            gabarito.append({
                "id_pagina": nome_arquivo, "id_elemento": "elemento-cancelar",
                "tipo_dp_esperado": "Obstrução", "origem": "sintetica",
                "detectado_manual": "", "detectado_sistema": "", "resultado_sistema": "", "resultado_manual": "",
            })


def gerar_controle(manifesto: dict, log: list, gabarito: list):
    rng = rng_para("controle", "hard_negativo")
    datas = manifesto["controle"]["hard_negativo"]["datas_promocao_real"]
    for i in range(N_INSTANCIAS_POR_NIVEL):
        data_escolhida = rng.choice(datas)
        nome_arquivo = f"controle_{i+1:02d}"
        html = preencher_template("controle_template.html", {"DATA_PROMOCAO": data_escolhida})
        caminho_pagina = PASTA_SAIDA_PAGINAS / f"{nome_arquivo}.html"
        if caminho_pagina.exists():
            continue  # protege página já gerada (pode já ter sido revisada no Momento 2)
        caminho_pagina.write_text(html, encoding="utf-8")

        log.append({
            "arquivo": nome_arquivo, "categoria": "controle", "nivel": "hard_negativo",
            "eh_hard_negative": "sim",
            "parametros": json.dumps({"data_promocao": data_escolhida}, ensure_ascii=False),
        })
        gabarito.append({
            "id_pagina": nome_arquivo, "id_elemento": "elemento-promo-real",
            "tipo_dp_esperado": "Nenhum", "origem": "sintetica",
            "detectado_manual": "", "detectado_sistema": "", "resultado_sistema": "", "resultado_manual": "",
        })
        gabarito.append({
            "id_pagina": nome_arquivo, "id_elemento": "elemento-newsletter-opcional",
            "tipo_dp_esperado": "Nenhum", "origem": "sintetica",
            "detectado_manual": "", "detectado_sistema": "", "resultado_sistema": "", "resultado_manual": "",
        })


def gerar_controle_mutacao(manifesto: dict, log: list, gabarito: list):
    rng = rng_para("controle_mutacao", "hard_negativo")
    opcoes = manifesto["controle_mutacao"]["hard_negativo"]["opcoes_cobranca_legitima"]
    for i in range(N_INSTANCIAS_POR_NIVEL):
        opcao = rng.choice(opcoes)
        nome_arquivo = f"controle_mutacao_{i+1:02d}"
        html = preencher_template("controle_mutacao_template.html", {
            "NOME_COBRANCA_LEGITIMA": opcao["nome"],
            "VALOR_COBRANCA": opcao["valor"],
        })
        caminho_pagina = PASTA_SAIDA_PAGINAS / f"{nome_arquivo}.html"
        if caminho_pagina.exists():
            continue  # protege página já gerada (pode já ter sido revisada no Momento 2)
        caminho_pagina.write_text(html, encoding="utf-8")

        log.append({
            "arquivo": nome_arquivo, "categoria": "controle_mutacao", "nivel": "hard_negativo",
            "eh_hard_negative": "sim",
            "parametros": json.dumps({"opcao_cobranca": opcao}, ensure_ascii=False),
        })
        gabarito.append({
            "id_pagina": nome_arquivo, "id_elemento": "elemento-frete-calculado",
            "tipo_dp_esperado": "Nenhum", "origem": "sintetica",
            "detectado_manual": "", "detectado_sistema": "", "resultado_sistema": "", "resultado_manual": "",
        })


def main():
    manifesto = carregar_manifesto()
    PASTA_SAIDA_PAGINAS.mkdir(parents=True, exist_ok=True)
    LOG_GERACAO_CSV.parent.mkdir(parents=True, exist_ok=True)

    log: list[dict] = []
    novas_linhas_gabarito: list[dict] = []

    gerar_furtividade(manifesto, log, novas_linhas_gabarito)
    gerar_acao_forcada(manifesto, log, novas_linhas_gabarito)
    gerar_obstrucao(manifesto, log, novas_linhas_gabarito)
    gerar_controle(manifesto, log, novas_linhas_gabarito)
    gerar_controle_mutacao(manifesto, log, novas_linhas_gabarito)

    campos_log = ["arquivo", "categoria", "nivel", "eh_hard_negative", "parametros"]
    log_existente = []
    if LOG_GERACAO_CSV.exists():
        log_existente = list(csv.DictReader(LOG_GERACAO_CSV.open(encoding="utf-8")))
    arquivos_ja_no_log = {l["arquivo"] for l in log_existente}
    log_novas_entradas = [l for l in log if l["arquivo"] not in arquivos_ja_no_log]
    log_completo = log_existente + log_novas_entradas

    with LOG_GERACAO_CSV.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos_log)
        escritor.writeheader()
        escritor.writerows(log_completo)

    # Anexa ao gabarito existente, sem apagar as linhas 'real' já rotuladas.
    linhas_existentes = list(csv.DictReader(GABARITO_CSV.open(encoding="utf-8")))
    ids_ja_sinteticos = {(l["id_pagina"], l["id_elemento"]) for l in linhas_existentes if l["origem"] == "sintetica"}
    linhas_novas_filtradas = [l for l in novas_linhas_gabarito if (l["id_pagina"], l["id_elemento"]) not in ids_ja_sinteticos]

    todas_as_linhas = linhas_existentes + linhas_novas_filtradas
    with GABARITO_CSV.open("w", encoding="utf-8", newline="") as f:
        campos = ["id_pagina", "id_elemento", "tipo_dp_esperado", "origem",
                  "detectado_manual", "detectado_sistema", "resultado_sistema", "resultado_manual"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(todas_as_linhas)

    print(f"{len(log)} página(s) sintética(s) geradas em {PASTA_SAIDA_PAGINAS}")
    print(f"Log de rastreabilidade salvo em {LOG_GERACAO_CSV}")
    print(f"{len(linhas_novas_filtradas)} nova(s) linha(s) adicionada(s) a {GABARITO_CSV} (origem=sintetica, já rotuladas automaticamente)")


if __name__ == "__main__":
    main()
