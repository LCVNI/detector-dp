"""
Módulo (b) — Extração semântica
--------------------------------------------------------------
Lê resultados/sinais_estruturais/*.json (saída do sensor TypeScript,
Etapa "a" da metodologia) e, para cada elemento captado, interpreta o
TEXTO associado usando o vocabulário de cada categoria de Dark Pattern.

Este módulo NÃO decide se algo é um dark pattern — ele só anota quais
termos semânticos aparecem no texto de um nó que o sensor já considerou
estruturalmente relevante. A decisão final (cruzamento estrutural x
semântico) é responsabilidade do módulo (c), classificador_correlacao.py.

Uso:
    python extrator_semantico.py
"""

import json
from pathlib import Path

from dicionario_categorias import (
    FURTIVIDADE_SUSPEITO,
    FURTIVIDADE_LEGITIMO,
    ACAO_FORCADA_SUSPEITO,
    OBSTRUCAO_SUSPEITO,
)

RAIZ = Path(__file__).resolve().parent.parent
PASTA_ENTRADA = RAIZ / "resultados" / "sinais_estruturais"
PASTA_SAIDA = RAIZ / "resultados" / "semantica_textual"


def _ocorrencias(texto_lower: str, radicais: list[str]) -> list[str]:
    return [r for r in radicais if r in texto_lower]


def extrair_semantica(elemento: dict) -> dict:
    """Aplica vocabulário de cada categoria SOMENTE aos padrões
    estruturais que o sensor já identificou como relevantes para aquele
    tipo de sinal — não roda vocabulário de Furtividade em elementos que
    o sensor nunca marcou como 'valor_monetario', por exemplo."""
    texto_lower = elemento.get("texto", "").lower()
    padroes = set(elemento.get("padroesDetectados", []))
    tags: list[str] = []
    evidencias: dict[str, list[str]] = {}

    if "valor_monetario" in padroes:
        susp = _ocorrencias(texto_lower, FURTIVIDADE_SUSPEITO)
        legit = _ocorrencias(texto_lower, FURTIVIDADE_LEGITIMO)
        if susp:
            tags.append("cobranca_financeira_periferica")
            evidencias["cobranca_financeira_periferica"] = susp
        elif legit:
            tags.append("cobranca_padrao_esperada")
            evidencias["cobranca_padrao_esperada"] = legit
        # se não bateu nem suspeito nem legítimo (ex.: preço puro de
        # produto, "R$ 259,00" sem nenhuma palavra ao redor), fica sem tag —
        # o módulo de correlação trata "sem tag semântica" como neutro.

    if "formato_temporal" in padroes:
        # Usa texto próprio + contexto do elemento pai: em marcações reais
        # (ex.: "Restam <span>02:00</span> para garantir..."), os dígitos e
        # a palavra de urgência costumam estar em nós DOM diferentes.
        texto_com_contexto = f"{texto_lower} {elemento.get('textoContexto', '').lower()}"
        urgencia = _ocorrencias(texto_com_contexto, ACAO_FORCADA_SUSPEITO)
        if urgencia:
            tags.append("urgencia_artificial")
            evidencias["urgencia_artificial"] = urgencia
        else:
            tags.append("formato_temporal_sem_urgencia")

    if "checkbox_pre_marcado" in padroes:
        # Fato estrutural inequívoco (opt-in já vem marcado) — não depende
        # de semântica para ser evidência de Ação Forçada, mas registramos
        # a tag para manter o mesmo formato de saída.
        tags.append("consentimento_pre_marcado")

    if "baixa_saliencia_visual" in padroes:
        retencao = _ocorrencias(texto_lower, OBSTRUCAO_SUSPEITO)
        if retencao:
            tags.append("linguagem_retencao")
            evidencias["linguagem_retencao"] = retencao

    confianca = round(min(0.95, 0.4 + 0.15 * sum(len(v) for v in evidencias.values())), 2) if evidencias else 0.3

    return {"tagsSemanticas": tags, "evidencias": evidencias, "confiancaSemantica": confianca}


def processar_todas_as_paginas() -> None:
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(PASTA_ENTRADA.glob("*.json"))
    print(f"Encontrados {len(arquivos)} JSON(s) de sinais estruturais em {PASTA_ENTRADA}")

    for arquivo in arquivos:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        for elemento in dados.get("elementosCaptados", []):
            elemento["semantica"] = extrair_semantica(elemento)

        saida = PASTA_SAIDA / arquivo.name
        saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

        n_com_tag = sum(1 for e in dados["elementosCaptados"] if e["semantica"]["tagsSemanticas"])
        print(f"  {dados['pagina']}: {len(dados['elementosCaptados'])} elemento(s), {n_com_tag} com tag semântica")

    print(f"\nJSONs enriquecidos com semântica salvos em {PASTA_SAIDA}")


if __name__ == "__main__":
    processar_todas_as_paginas()
