#!/usr/bin/env bash
# ------------------------------------------------------------------
# Orquestra o pipeline completo de detecção (Etapas 2 e 3):
#   1) Sensor estrutural (TypeScript)          -> resultados/sinais_estruturais/
#   2) Extração semântica (Python)             -> resultados/semantica_textual/
#   3) Classificador de correlação (Python)    -> resultados/decisao_final/
#   4) Comparação com o gabarito (Python)      -> resultados/tabela_resultados.csv
#      (calcula métricas SE o gabarito já estiver rotulado; senão, avisa
#      quais linhas ainda faltam e para por aí — Momento 1/2 são manuais)
#
# Uso:
#   ./pipeline/rodar_pipeline.sh
#
# Pré-requisitos (rodar uma vez por máquina, não a cada execução):
#   cd detector-ts && npm install
#   pip install --break-system-packages scikit-learn statsmodels pandas
# ------------------------------------------------------------------
set -e

RAIZ_PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ_PROJETO"

echo "============================================================"
echo "[1/4] Sensor estrutural (TypeScript) — só sinais, sem decisão"
echo "============================================================"
cd "$RAIZ_PROJETO/detector-ts"
npx tsc -p tsconfig.json
node dist/detector.js

echo ""
echo "============================================================"
echo "[2/4] Extração semântica (Python) — interpreta o texto captado"
echo "============================================================"
cd "$RAIZ_PROJETO/classificador-py"
python3 extrator_semantico.py

echo ""
echo "============================================================"
echo "[3/4] Classificador de correlação (Python) — decisão final"
echo "============================================================"
python3 classificador_correlacao.py

echo ""
echo "============================================================"
echo "[4/4] Comparação com o gabarito (Etapa 4)"
echo "============================================================"
cd "$RAIZ_PROJETO/pipeline"
python3 comparar_com_gabarito.py

echo ""
echo "Pipeline concluído. Veja resultados/tabela_resultados.csv"
