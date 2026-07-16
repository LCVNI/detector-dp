# Tabela comparativa — valores reais do protótipo

## Situação 1 — Só dados reais

| Indicador | Condição A (Manual) | Condição B (Automático) |
|---|---|---|
| Precisão | 0.65 | 1.00 |
| Recall | 0.65 | 1.00 |
| F1-Score | 0.65 | 1.00 |

_n manual=13, n sistema=12_

McNemar (situação 1): estatística=0.000, p=0.2500 → sem diferença estatisticamente significativa

## Situação 2 — Só dados sintéticos

| Indicador | Condição A (Manual) | Condição B (Automático) |
|---|---|---|
| Precisão | 1.00 | 0.90 |
| Recall | 1.00 | 0.81 |
| F1-Score | 1.00 | 0.82 |

_n manual=8, n sistema=66_

McNemar (situação 2): estatística=0.000, p=1.0000 → sem diferença estatisticamente significativa

## Situação 3 — Agregado (real + sintético)

| Indicador | Condição A (Manual) | Condição B (Automático) |
|---|---|---|
| Precisão | 0.79 | 0.91 |
| Recall | 0.79 | 0.84 |
| F1-Score | 0.79 | 0.85 |

_n manual=21, n sistema=78_

McNemar (situação 3): estatística=1.000, p=0.6250 → sem diferença estatisticamente significativa

---

**Leitura obrigatória (Ameaças à Validade — validade de construção):** as métricas da Situação 2 e 3 incluem dados sintéticos, que compartilham template com o que calibrou as heurísticas do detector — há risco de circularidade residual mesmo com a Regra R2 (vocabulário parcialmente distinto). Reportar as 3 situações separadamente, como acima, é o que permite ao leitor avaliar se a conclusão se sustenta nos dados reais isoladamente (Situação 1), não só no agregado.