# Prompt de Implementação — Detecção de Dark Patterns (Trabalho 3, Grupo 4)

## Contexto para o assistente de código
Estou desenvolvendo, para uma disciplina de Metodologia da Pesquisa, um protótipo de detecção de Dark Patterns em páginas de e-commerce. O protótipo é o piloto reduzido do projeto de pesquisa "Ferramenta Automatizada em Tempo Real para Detecção de Dark Patterns Críticos". Preciso implementar de fato:

1. Um conjunto de páginas HTML simulando e-commerce, algumas com Dark Patterns (Furtividade, Obstrução, Ação Forçada) e algumas neutras (controle).
2. Um detector estrutural em TypeScript que observa a DOM (MutationObserver) e aplica heurísticas.
3. Um classificador textual em Python que analisa o texto associado aos elementos suspeitos (urgência artificial, taxas ocultas, linguagem indutora).
4. Um pipeline que roda os dois módulos sobre as páginas, gera um CSV de resultados (VP/FP/FN/VN) e calcula Precisão, Recall e F1-Score comparando com uma classificação manual (gabarito).
5. O gráfico e a tabela finais para o artigo, além do teste de McNemar comparando detecção manual x automática.

Os dados do "Parcial 2" (40 observações, mistas reais+sintéticas) foram usados como piloto exploratório, mas para a entrega final preciso de evidência real gerada pelo próprio protótipo rodando sobre páginas que eu de fato construí — não posso apresentar apenas números simulados como se fossem execução real.

---

## Etapa 0 — Estrutura do repositório
Crie a seguinte estrutura de pastas:
```
detector-dp/
├── paginas/            # páginas HTML de teste (base + sintéticas)
├── gabarito/           # rótulos.csv (gabarito, real e sintético)
├── detector-ts/        # detector estrutural (TypeScript)
├── classificador-py/   # classificador textual (Python)
├── pipeline/           # orquestração + métricas
├── resultados/         # CSV, gráficos, tabela final
└── material-artigo/    # tabela e gráfico prontos para o artigo
```

## Onde a análise humana é necessária (visão geral dos checkpoints)
Nem tudo neste projeto é automatizável — e o barema valoriza justamente reconhecer isso com clareza, em vez de tratar o pipeline como se rodasse sozinho do início ao fim. São 4 momentos em que uma pessoa do grupo precisa parar e fazer um julgamento manual, cada um com um objetivo diferente:

| # | Momento | Quando acontece | Quem faz | Objetivo |
|---|---|---|---|---|
| 1 | Rotulagem das páginas reais | Logo depois de construir as 5 páginas-base (Etapa 1) | Um revisor **diferente** de quem construiu a página | Criar o gabarito real + a Condição A Manual (real) |
| 2 | Revisão cega das páginas sintéticas | Depois de rodar o gerador (Etapa 1.5) | Um integrante que **não gerou** aquela instância específica | Criar a Condição A Manual (sintético) + medir a taxa de concordância (Regra R7) |
| 3 | Checagem dos resultados do protótipo | Depois do pipeline automático rodar (Etapa 4) | Todo o grupo, em conjunto (é o "Checklist Manual" já citado no Parcial 1) | Confirmar que os VP/FP/FN/VN fazem sentido antes de ir pro artigo — pegar erro sistemático óbvio |
| 4 | Interpretação estatística e redação | Fase final de redação (Etapa 6) | Todo o grupo | Interpretar as 3 situações do McNemar (real/sintético/agregado) e reconhecer limitações honestamente |

Abaixo, como executar cada um desses testes na prática.

### Momento 1 — Rotulagem manual das páginas reais
**Por que precisa ser uma pessoa diferente de quem construiu:** quem constrói a página já sabe onde colocou o dark pattern — se essa mesma pessoa "rotular", não está medindo percepção real, só confirmando a própria intenção de design.

**Como fazer:**
1. Distribua as 5 páginas-base entre os integrantes de forma cruzada: quem construiu a página de Furtividade não é quem a rotula, por exemplo.
2. O revisor abre a página **sem consultar** as notas de design/RSL usadas na construção, como se estivesse navegando num site desconhecido.
3. Ele lista os elementos que considera suspeitos e atribui uma categoria (Furtividade/Obstrução/Ação Forçada/nenhum) — tempo sugerido: 2-3 minutos por página, simulando a atenção real de um usuário, não uma auditoria minuciosa.
4. Preferível ter **2 revisores independentes** por página (se o grupo tiver 4-5 pessoas, dá pra formar duplas) — quando os dois concordam, o gabarito fica mais robusto; quando discordam, isso vira material para a seção de Ameaças à Validade (validade interna: "viés na rotulação manual", já apontado no Parcial 1).
5. Resultado vai para `gabarito/rotulos.csv` (origem=real) e alimenta a Condição A (Manual) da tabela de comparação.

### Momento 2 — Revisão cega das páginas sintéticas
**Como fazer:**
1. Antes de entregar as páginas sintéticas para revisão, renomeie os arquivos para IDs neutros (ex.: `revisao_01.html`, `revisao_02.html`) e embaralhe a ordem — o revisor não pode ver o nome do template nem a categoria que o gerador usou.
2. O revisor designado (que não gerou aquele lote) preenche uma planilha simples: `id_pagina | elementos_suspeitos | categoria_atribuida`.
3. Depois da revisão, compare com o gabarito automático (Etapa 1.5) para dois fins ao mesmo tempo: (a) preencher `detectado_manual` para a Condição A do subconjunto sintético; (b) calcular a taxa de concordância da Regra R7 (quantas o revisor bateu com o rótulo do gerador).

### Momento 3 — Checklist manual de checagem dos resultados
Esse é o instrumento que o próprio grupo já havia planejado no Parcial 1 ("Checklist Manual — Validar os resultados obtidos pelo protótipo"). Depois que o pipeline gerar `resultados/tabela_resultados.csv`:
1. Escolham uma amostra (ex.: 20-30% das linhas) e confiram manualmente se o VP/FP/FN/VN atribuído bate com o que vocês esperariam olhando a página.
2. Procurem padrões de erro óbvios (ex.: o sistema marca "detectado" em praticamente tudo, o que infla Recall artificialmente à custa de Precisão).
3. Esse checkpoint é rápido (não é rotular tudo de novo), serve só como controle de qualidade antes de fechar os números que vão pro artigo.

### Momento 4 — Interpretação e redação
Não é um "teste" no sentido técnico, mas exige julgamento humano insubstituível: decidir o que os três cenários do McNemar (Situação 1/2/3 da Etapa 4) significam para a hipótese do grupo, e redigir a seção de Limitações reconhecendo onde os dados sintéticos podem estar inflando o resultado. Isso deve ser feito coletivamente, já que a especificação exige que "todos os integrantes demonstrem domínio mínimo do trabalho" na apresentação final.



## Etapa 1 — Construir o corpus de páginas de teste (dados mistos, conforme já declarado no Parcial 2)
O Parcial 2 já declarou explicitamente **dados mistos**: parte real (páginas testadas em modo piloto) e parte sintética (gerada para ampliar cobertura). Para manter coerência com o que foi entregue, a base de páginas deve seguir a mesma lógica, não um corpus novo do zero:

**1) 5 páginas-base "reais"** — construídas a partir da observação de páginas reais de e-commerce (pode ser HTML próprio inspirado/recriado a partir de exemplos observados, já que reproduzir DOM de sites reais teria implicações de direitos autorais/ToS; o importante é que a *estrutura e o comportamento* sejam fiéis ao que foi observado):
   - 1 página com **apenas Furtividade** (ex.: item extra adicionado sozinho ao carrinho, taxa que só aparece no passo final).
   - 1 página com **apenas Obstrução** (ex.: botão de cancelar assinatura escondido/exige múltiplos cliques).
   - 1 página com **apenas Ação Forçada** (ex.: checkbox pré-marcado para newsletter/upsell, contagem regressiva falsa).
   - 1 página neutra (controle, sem dark pattern) — necessária para gerar Falsos Positivos/Verdadeiros Negativos reais.
   - **1 página "combinada"/realista**, com os 3 dark patterns coexistindo na mesma tela de checkout (ex.: checkbox de upsell pré-marcado + contagem regressiva falsa de "restam 2 minutos" + botão de cancelar assinatura oculto atrás de um link cinza-claro). Essa página é a que mais se aproxima de um cenário real — sites raramente usam um dark pattern isolado — e serve para testar se o classificador híbrido consegue diferenciar múltiplos padrões coexistindo sem confundi-los.

As páginas isoladas continuam necessárias: elas funcionam como **calibração** — servem para medir a precisão do detector em cada categoria isoladamente antes de testar o cenário combinado, que é mais difícil.

**2) Expansão sintética a partir dessas 5 páginas-base** — gerar variações programáticas (trocar textos, posições, cores, tempos de mutação) das mesmas categorias, incluindo variações da página combinada, até atingir o volume de observações desejado (ex.: as 40 observações citadas no Parcial 2, ou um número menor e honesto se o prazo não permitir). Cada variação sintética deve ser marcada com uma flag `origem: "sintetica"` no gabarito, para que o artigo consiga separar claramente resultado real vs. sintético na análise — é exatamente essa distinção que a especificação exige declarar.

**Mudança importante no gabarito por causa da página combinada:** como uma mesma página agora pode conter mais de um dark pattern, o gabarito não pode mais ser "1 rótulo por página" — precisa ser **por elemento**. Estrutura sugerida em `gabarito/rotulos.csv`:

| id_pagina | id_elemento | tipo_dp_esperado | origem | detectado_manual | detectado_sistema | resultado |
|---|---|---|---|---|---|---|
| pagina_combinada_01 | elemento_checkbox | Ação Forçada | real | Sim | Sim | VP |
| pagina_combinada_01 | elemento_timer | Furtividade | real | Sim | Não | FN |
| pagina_combinada_01 | elemento_cancelar | Obstrução | real | Sim | Sim | VP |

Isso também muda a métrica: Precisão/Recall/F1 passam a ser calculados **por elemento detectado**, não por página — o que é mais rigoroso e mais próximo de como um sistema real seria avaliado.

Cada página (real ou sintética) deve ter, além do gabarito por elemento, um atributo oculto `data-dp-origem="real"` / `"sintetica"` — isso NÃO pode ser lido pelo detector; serve só para a análise separar dados reais de sintéticos.

**Peça ao assistente:** "gere as 5 páginas HTML-base (Furtividade isolada, Obstrução isolada, Ação Forçada isolada, Controle, e uma página Combinada com os 3 padrões coexistindo) simulando checkout de loja online, com o comportamento enganoso implementado via JS (mutação real da DOM); depois gere um script que cria N variações sintéticas de cada uma, alterando textos/tempos/posições e marcando `data-dp-origem='sintetica'`".

## Etapa 1.5 — Geração de dados sintéticos (metodologia)

**Princípio central:** a rotulagem manual só é necessária para as páginas reais (as 5 base), porque ali o rótulo depende de julgamento humano sobre o que foi observado. Nas páginas sintéticas, o rótulo nasce automaticamente — é o próprio gerador que decide, por construção, qual dark pattern foi inserido em cada variação. É isso que permite elevar a amostra sem multiplicar o trabalho de rotulagem manual. O detector (Etapas 2 e 3) roda exatamente igual nos dois casos: ele não recebe nem usa a informação de origem, só analisa a DOM/texto da página como faria em qualquer site.

**Como implementar (abordagem template + manifesto):**

1. **Templates parametrizados** — cada uma das 5 páginas-base vira um template HTML/JS com "slots" substituíveis: texto do timer de urgência, nome do produto do upsell, tempo (ms) até a mutação da DOM ocorrer, cor do botão, técnica de ocultação do botão de cancelar (display:none, opacity:0, z-index negativo, tamanho de fonte reduzido), posição do checkbox pré-marcado.

2. **Manifesto de variação** (`manifesto_sintetico.json`) — lista os valores possíveis para cada slot, por categoria de dark pattern, já incluindo nível de dificuldade (R3) e hard negatives (R4). Exemplo:
```json
{
  "furtividade": {
    "obvio": {
      "tempo_mutacao_ms": [500],
      "texto_taxa": ["Taxa de conveniência (obrigatória)"],
      "posicao_insercao": ["depois_total"]
    },
    "sutil": {
      "tempo_mutacao_ms": [3000],
      "texto_taxa": ["Ajuste de processamento"],
      "posicao_insercao": ["resumo_lateral"]
    }
  },
  "acao_forcada": {
    "obvio": { "texto_urgencia": ["Restam 2 minutos!"], "checkbox_pre_marcado": true },
    "sutil": { "texto_urgencia": ["Estoque limitado nesta região"], "checkbox_pre_marcado": true }
  },
  "hard_negativo": {
    "descricao": "elementos que parecem dark pattern mas não são",
    "exemplos": [
      "contador regressivo de promoção real com data/hora fixa e verificável",
      "checkbox de newsletter visualmente destacado mas desmarcado por padrão"
    ]
  }
}
```

**Importante (R2):** os textos usados aqui (`texto_taxa`, `texto_urgencia`) devem vir de um pool de vocabulário *diferente* do dicionário de palavras-chave do classificador Python (Etapa 3) — ex.: se o classificador procura por "taxa de conveniência", o gerador deve poder produzir também "ajuste de processamento", "custo adicional de manuseio" etc., para que a detecção não seja garantida por coincidência de string.

3. **Script gerador** (`pipeline/gerar_sinteticos.py` ou `.ts`) — lê os templates + manifesto, combina os slots (todas as combinações ou uma amostra aleatória de N combinações por categoria), grava cada HTML gerado em `paginas/sinteticas/`, e **já escreve a linha correspondente em `gabarito/rotulos.csv`** com `origem=sintetica` e o rótulo correto — sem intervenção manual.

4. **Checagem de sanidade (não é rotulagem manual completa):** revisar visualmente uma amostra pequena (ex.: 3-5 páginas sintéticas) só para confirmar que o gerador não produziu HTML quebrado ou um padrão irreconhecível — isso é controle de qualidade do gerador, não rotulagem de conteúdo.

### Regras para dar credibilidade metodológica à geração sintética
*(Lembrando: "o manifesto" citado abaixo é o `manifesto_sintetico.json` definido no item 2 da Etapa 1.5 acima — o arquivo que lista, por categoria de dark pattern, os valores possíveis de cada slot variável do template, como texto de urgência, técnica de ocultação, tempo de mutação etc.)*

Template + manifesto resolve o mecanismo, mas não garante rigor por si só. Duas armadilhas comuns em dados sintéticos são parecer arbitrário e ser circular (gerar exatamente o que o próprio detector procura, inflando o resultado). Regras para evitar isso:

**R1 — Ancoragem rastreável, nada "inventado do nada".** Cada valor usado no manifesto (texto de urgência, técnica de ocultação, nome do upsell) precisa ter origem documentada: ou veio de um dos 11 estudos da RSL do grupo (Dickinson 2024; Liang, Hossain e Brown, 2025; etc.), ou foi observado diretamente numa das 5 páginas reais-base. Nada de gerar frases/valores aleatórios sem relação com o que a literatura ou a observação real documentaram — isso é o que separa "simulação metodologicamente justificada" de invenção, exigência explícita da especificação.

**R2 — Vocabulário de geração ≠ vocabulário de detecção (evita circularidade).** O pool de textos usados para *gerar* os dark patterns sintéticos (Etapa 1.5) não pode ser a mesma lista de palavras-chave usada pelo classificador Python para *detectar* (Etapa 3). Construa dois pools distintos: um vocabulário mais amplo de geração (sinônimos, variações de fraseado observadas na literatura/sites reais) que só se sobrepõe parcialmente ao dicionário de heurísticas do detector. Se as duas listas forem idênticas, o resultado de Precisão/Recall nos sintéticos não tem valor probatório — só mostra que o gerador e o detector concordam consigo mesmos.

**R3 — Variar o nível de dificuldade (óbvio x sutil).** Para cada categoria, gerar tanto instâncias óbvias (ex.: contraste de cor extremo, texto de urgência explícito) quanto sutis (ex.: diferença de cor pequena, linguagem mais discreta) — testa se as heurísticas generalizam além do caso mais fácil, que é o que a literatura aponta como fragilidade dos métodos atuais (GOWTHAM et al., 2024; KIRTHIGA et al., 2024).

**R4 — Incluir "negativos difíceis" (hard negatives).** Gerar também elementos que se *parecem* com um dark pattern mas não são um (ex.: contador regressivo de uma promoção genuinamente limitada, checkbox opcional visualmente destacado mas não pré-marcado). Sem isso, a página de controle vira só "página vazia sem nada suspeito", o que superestima artificialmente a precisão — um sistema real precisa diferenciar urgência genuína de urgência falsa, não só "tem elemento" x "não tem elemento".

**R5 — Balanceamento de classes.** Gerar quantidades semelhantes de instâncias sintéticas por categoria (Furtividade, Obstrução, Ação Forçada, Controle, Combinada) — evitar que uma categoria domine a amostra, o que distorceria Precisão/Recall agregados.

**R6 — Reprodutibilidade e rastreabilidade.** Fixar uma seed de geração (ex.: `random.seed(42)`) e manter um log (`resultados/log_geracao.csv`) registrando, para cada arquivo gerado: combinação exata de parâmetros do manifesto, categoria, nível de dificuldade (R3), e se é hard negative (R4). Isso permite reconstruir o dataset e é o tipo de rastreabilidade que sustenta a seção de Método do artigo quando questionada.

**R7 — Relatar a taxa de concordância da checagem de sanidade (item 4 acima).** Ao revisar a amostra manual, registrar quantas páginas sintéticas o revisor humano concorda serem exemplos plausíveis do padrão pretendido (ex.: "18/20 = 90% de concordância"). Isso funciona como uma mini-validação da qualidade do gerador e pode ser citado no artigo como evidência de que os dados sintéticos são plausíveis, não arbitrários.

### Como o dado sintético é usado na prática: os dois papéis do "manual" (exemplo)
Existe um ponto que gera confusão e precisa ficar explícito: **gabarito (ground truth) e "Condição A Manual" não são a mesma coisa**, embora nas páginas reais elas nasçam juntas.

- **Gabarito** = o rótulo que consideramos "a verdade" sobre a página, usado para julgar se o sistema acertou (VP/FP/FN/VN).
- **Condição A "Manual"** = o desempenho de uma pessoa tentando encontrar os dark patterns sozinha, sem saber o gabarito — é o "baseline humano" com que o sistema é comparado (conforme já estabelecido no Parcial 2).

Nas páginas **reais**, as duas coisas se confundem: quando alguém do grupo observa a página e decide o que é dark pattern, essa decisão já É o gabarito e já É o desempenho manual, ao mesmo tempo.

Nas páginas **sintéticas**, isso se separa — e por isso ainda é preciso um passo manual, mesmo nelas:
- O **gabarito nasce automático**, direto do manifesto usado para gerar a página (não precisa de revisão humana pra "descobrir" o que está lá, porque quem gerou já sabe).
- Mas a **Condição A "Manual"** só é válida se um integrante do grupo revisar a página **sem saber qual combinação do manifesto foi usada** (revisor cego) — senão a "medição manual" é só reler o próprio gabarito, o que não mede nada.

**Exemplo passo a passo:**
1. O gerador cria `sint_acaoforcada_03.html` (categoria = Ação Forçada, dificuldade = sutil, texto = "Estoque limitado nesta região", checkbox pré-marcado). Isso já grava automaticamente em `gabarito.csv`: `tipo_esperado = Ação Forçada`, `origem = sintetica` — nenhuma revisão humana necessária aqui.
2. **Rodada automática:** o pipeline TS+Python roda normalmente sobre a página (ele não sabe que é sintética) → produz `detectado_sistema`.
3. **Rodada manual cega:** um integrante que **não** gerou essa instância específica (ou que revisa uma lista embaralhada, sem acesso ao manifesto/nome do arquivo) abre a página e marca o que acha suspeito → produz `detectado_manual`.
4. As três colunas (`tipo_esperado`, `detectado_sistema`, `detectado_manual`) alimentam `tabela_resultados.csv`: o par (`tipo_esperado` x `detectado_sistema`) gera o VP/FP/FN/VN do sistema; o par (`tipo_esperado` x `detectado_manual`) gera o desempenho da Condição A; e os dois juntos alimentam o McNemar (Etapa 4).

**Sobre garantir que as páginas sintéticas estão "no mesmo nível" das reais:** isso não é algo que se garante de antemão — é algo que se aproxima (via R1 e R3) e depois se mede empiricamente (via R7, a taxa de concordância do revisor cego). Se a concordância for baixa numa categoria, isso não é escondido: vira uma limitação declarada na seção de Ameaças à Validade do artigo, em vez de uma premissa assumida sem evidência.

**Peça ao assistente:** "escreva um script Python (com `random.seed(42)` fixa) que lê os templates HTML das 5 páginas-base com placeholders tipo `{{TEMPO_MUTACAO}}`, combina com os valores de manifesto_sintetico.json (incluindo variações óbvias, sutis e hard negatives), gera as páginas sintéticas em paginas/sinteticas/, grava um log de rastreabilidade em resultados/log_geracao.csv com a combinação exata de parâmetros usada em cada arquivo, e já adiciona automaticamente as linhas correspondentes em gabarito/rotulos.csv com origem='sintetica' e o rótulo esperado. Use um pool de vocabulário para os textos gerados que seja diferente da lista de palavras-chave do classificador da Etapa 3."

**O que precisa ser declarado no artigo/documento de dados sintéticos (exigência da especificação):**
- **Como os dados foram gerados:** processo de template + manifesto descrito acima (não é geração aleatória "solta" — é uma recombinação controlada de variações observadas nas páginas reais).
- **Hipóteses embutidas:** (1) assume-se que variar textura de superfície (texto, cor, tempo, posição) não muda a categoria estrutural do dark pattern; (2) assume-se que as heurísticas calibradas nas páginas reais generalizam para essas variações.
- **Limitação que isso impõe:** como os dados sintéticos derivam dos mesmos templates usados para desenhar as heurísticas do detector, há risco de circularidade — o desempenho medido nos sintéticos tende a ser otimista em relação a um dark pattern genuinamente novo "in the wild". Por isso, **as métricas finais devem ser reportadas separadamente para o subconjunto real e o sintético**, nunca só agregadas — isso deve constar na seção de Ameaças à Validade (validade de construção) do artigo.

## Etapa 2 — Detector estrutural (TypeScript)
Implemente em `detector-ts/`:
- Um `MutationObserver` que roda quando a página é carregada (via Puppeteer ou jsdom, para rodar headless em lote sobre todas as páginas de `paginas/`).
- Heurísticas simples baseadas em seletores CSS/XPath: elementos inseridos fora de uma ação do usuário, botões com contraste de cor típico de dark pattern, checkboxes pré-marcados, elementos com `display:none` aplicado a botões de "cancelar"/"recusar".
- Saída: um JSON por página com `{pagina, elementosSuspeitos: [...], tipoDetectado}`.

**Peça ao assistente:** "implemente um script Node/TypeScript usando Puppeteer que abre cada arquivo HTML da pasta paginas/, ativa um MutationObserver por 3 segundos, e salva um JSON com os elementos que sofreram mutação suspeita".

## Etapa 3 — Classificador textual (Python)
Implemente em `classificador-py/`:
- Recebe o texto associado a cada elemento suspeito (do JSON gerado na Etapa 2).
- Classifica com heurísticas de palavras-chave (ou um classificador simples tipo Naive Bayes/regras) para termos de urgência artificial ("restam apenas", "últimas unidades"), cobrança periférica ("taxa de conveniência", "seguro incluído") etc.
- Saída: mesmo JSON enriquecido com `classificacaoTextual` e `confianca`.

**Peça ao assistente:** "escreva um classificador Python simples baseado em lista de palavras-chave por categoria (Furtividade, Obstrução, Ação Forçada) que recebe uma string e retorna a categoria mais provável".

## Etapa 4 — Pipeline de correlação e métricas
Em `pipeline/`:
- Junta a saída do TypeScript (estrutural) com a do Python (textual) → decide se é um Dark Pattern crítico (regra de correlação, conforme a metodologia do projeto original).
- Compara com `gabarito/rotulos.csv` **por elemento** (não por página, já que a página combinada tem múltiplos elementos com dark patterns diferentes) → gera `resultados/tabela_resultados.csv` com colunas como no exemplo do Parcial 1, mas com uma linha por elemento avaliado (`ID, Página, ID Elemento, Tipo Esperado, Detectado Manualmente, Detectado Pelo Sistema, Resultado [VP/FP/FN/VN]`).
- Calcula Precisão, Recall, F1-Score (pode usar `sklearn.metrics`), tanto agregado quanto **quebrado por categoria de dark pattern** e **quebrado por origem (real x sintético)** — essa separação é obrigatória dado o risco de circularidade explicado na Etapa 1.5 (o desempenho nos sintéticos tende a ser otimista). Comparar o desempenho na página isolada x na página combinada, e no subconjunto real x sintético, são os dois pontos de discussão mais fortes do artigo.
- Roda o **teste de McNemar** (já prometido no Parcial 2) com `statsmodels` ou `scipy`, comparando classificação manual x automática pareada por elemento. Assim como as métricas de Precisão/Recall/F1 (acima), o teste deve ser rodado **três vezes**: (1) só no subconjunto real, (2) só no subconjunto sintético, (3) agregado com todos os dados. Isso é necessário pelo mesmo motivo da separação nas métricas: se o McNemar só for calculado no agregado, um resultado significativo pode estar sendo "carregado" pelo volume maior de dados sintéticos (que tendem a favorecer o detector, pelo risco de circularidade da Regra R2) e mascarar um resultado não significativo no subconjunto real, que é o que realmente importa como evidência empírica.

**Peça ao assistente:** "escreva um script Python que lê tabela_resultados.csv e rotulos.csv (nível de elemento), calcula precisão/recall/F1 agregado, por categoria e por origem (real/sintético) com sklearn, e aplica o teste de McNemar com statsmodels.stats.contingency_tables três vezes: no subconjunto real, no sintético e no agregado."

### Exemplo de como as 3 tabelas ficam no artigo (com valores fictícios, substituir pelos reais)

**Situação 1 — Só dados reais** (a evidência que mais importa, mesmo sendo a menor amostra)

| Indicador | Condição A (Manual) | Condição B (Automático) |
|---|---|---|
| Precisão | 0,80 | 0,75 |
| Recall | 0,70 | 0,72 |
| F1-Score | 0,75 | 0,73 |

McNemar (real): p = 0,62 → sem diferença estatisticamente significativa (amostra pequena)

**Situação 2 — Só dados sintéticos**

| Indicador | Condição A (Manual) | Condição B (Automático) |
|---|---|---|
| Precisão | 0,79 | 0,88 |
| Recall | 0,72 | 0,84 |
| F1-Score | 0,75 | 0,86 |

McNemar (sintético): p = 0,03 → diferença significativa favorecendo o Automático

**Situação 3 — Agregado (real + sintético)**

| Indicador | Condição A (Manual) | Condição B (Automático) |
|---|---|---|
| Precisão | 0,79 | 0,85 |
| Recall | 0,71 | 0,80 |
| F1-Score | 0,75 | 0,82 |

McNemar (agregado): p = 0,04 → diferença significativa

**Como interpretar (o que deve ir na Discussão do artigo):** se as 3 situações forem reportadas juntas e o padrão acima se confirmar, a leitura honesta é: "o sistema mostrou ganho estatisticamente significativo apenas quando o volume foi ampliado com dados sintéticos; nos dados reais observados isoladamente, ainda não há evidência suficiente para essa conclusão". Reportar só a Situação 3 (agregada) esconderia que a significância está sendo "puxada" pelo subconjunto sintético — é justamente esse tipo de transparência que separa "reconhecer limitações" de "inflar resultado", conforme os critérios de avaliação da especificação.

## Etapa 5 — Tabela e gráfico finais
- Gerar novamente a tabela comparativa (Precisão/Recall/F1 — Manual x Automático), agora com números reais do pipeline, não mais simulados.
- Gerar o gráfico de barras (mesmo estilo do Parcial 2) com `matplotlib`, salvando em `material-artigo/`.

## Etapa 6 — Redação do artigo (usar a estrutura obrigatória da especificação)
Com os resultados reais em mãos, preencher:
1. Introdução curta (já praticamente pronta a partir do Projeto de Pesquisa).
2. Método/Plano de validação (baseado no Parcial 1, ajustado ao que foi de fato executado).
3. Resultados (tabela + gráfico + McNemar).
4. Discussão (o que os números realmente sustentam da hipótese).
5. Limitações e ameaças à validade (conclusão, interna, externa, construção — já esboçadas no Parcial 1/2).
6. Conclusão.
7. Referências (já existem no Trabalho 2).

**Importante (regra da especificação):** se parte dos dados continuar sendo sintética (por falta de tempo para testar em 100 e-commerces reais), isso precisa estar declarado explicitamente no artigo, com a frase sugerida pela especificação — não pode ser apresentado como evidência empírica real.

## Etapa 7 — Empacotar entregáveis (checagem final)
- [ ] Artigo em PDF
- [ ] Slides
- [ ] Base de dados (.csv) gerada pelo pipeline real
- [ ] Script/notebook (TS + Python) usados
- [ ] Documento curto explicando a geração dos dados sintéticos (se ainda houver)

---

### Prioridade sugerida dado o prazo (15/07)
Como o tempo é curto, a ordem de maior retorno é: **Etapa 1 (as 5 páginas-base primeiro — priorize a página combinada e a de controle, que sozinhas já geram VP/FP/FN/VN reais — só depois pensar em expansão sintética) → Etapa 2 (heurísticas simples primeiro) → Etapa 3 (classificador por palavra-chave, não precisa de ML de verdade) → Etapa 4 (métricas) → Etapa 5/6**. Um pipeline pequeno mas real, rodando sobre as páginas-base de verdade, vale mais para o barema do que um número grande de páginas majoritariamente sintéticas.
