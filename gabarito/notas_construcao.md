# Notas de construção — páginas-base (real)

> ⚠️ Uso interno da equipe de construção. **Não mostrar a quem for rotular
> (Momento 1)** — o revisor deve abrir as páginas sem consultar este
> documento, como se navegasse num site desconhecido.

Cada linha abaixo é a **intenção de design**, ancorada em literatura (Regra R1),
não o gabarito. O gabarito real só nasce depois da rotulagem cega feita por um
integrante diferente de quem construiu a página.

| Página | Categoria pretendida | id_elemento | Referência de ancoragem |
|---|---|---|---|
| `furtividade.html` | Furtividade | `elemento-taxa-oculta` | Gray et al. (2018) — sneaking: ocultar/atrasar divulgação de informação relevante |
| `obstrucao.html` | Obstrução | `elemento-cancelar` | Gray et al. (2018) — obstruction: tornar processo mais difícil do que precisa para dissuadir ação |
| `acaoforcada.html` | Ação Forçada | `elemento-timer`, `elemento-checkbox-preselecionado` | Gray et al. (2018) — forced action; Mathur et al. (2019) — uso de urgência artificial na venda |
| `controle.html` | Nenhuma (controle) | `elemento-promo-real` (hard negative), `elemento-newsletter-opcional` (hard negative) | Regra R4 do plano — negativos difíceis: promoção real verificável e checkbox opcional desmarcado |
| `controle_mutacao.html` | Nenhuma (controle — **hard negative estrutural**) | `elemento-frete-calculado` | Extensão da Regra R4 ao nível estrutural: mutação real de DOM com valor monetário, mas transparente (placeholder desde o 1º render, nome de cobrança padrão "Frete", sem urgência). **Dispara falso positivo na Etapa 2 isolada (furtividade) por desenho** — serve para provar que a Etapa 3 (texto) + Etapa 4 (correlação) são necessárias, não opcionais |
| `combinada.html` | Furtividade + Obstrução + Ação Forçada | `elemento-taxa-oculta`, `elemento-cancelar`, `elemento-timer`, `elemento-checkbox-preselecionado` | Combinação dos três acima, coexistindo na mesma tela de checkout |

## Como usar isto na Etapa de rotulagem (Momento 1)
1. Distribuir cruzado: quem construiu não rotula a própria página.
2. Revisor abre o HTML renderizado (não o código-fonte) e lista o que acha suspeito, com categoria.
3. Comparar o rótulo do revisor com este documento **depois** da rotulagem, nunca antes.
4. Preencher `gabarito/rotulos.csv` com o resultado da rotulagem humana — este arquivo aqui é só rastreabilidade de design (Regra R1/R6), não substitui a rotulagem.

## Achado registrado durante a implementação (vale citar no artigo)
Ao construir `controle_mutacao.html`, a Etapa 2 (detector estrutural) rodou de fato e
marcou essa página como suspeita de Furtividade — um **falso positivo real e reproduzível**
da heurística estrutural isolada (`elemento com valor monetário inserido via mutação`).
Isso não é um bug a esconder: é evidência empírica de que o detector estrutural sozinho
não basta, e de que a correlação Etapa 2 + Etapa 3 (Etapa 4) é uma exigência metodológica,
não um refinamento opcional. Recomenda-se citar esse caso concreto na seção de Resultados/
Discussão do artigo como justificativa da arquitetura híbrida do protótipo.
