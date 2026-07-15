/**
 * Sensor estrutural (Etapa 2) — reescrito para separar estritamente
 * "sensoriamento" de "decisão", conforme a metodologia do projeto:
 *
 *   (a) Sensor (este arquivo): MutationObserver + varredura de padrões
 *       SINTÁTICOS/estruturais (nunca vocabulário/semântica de palavras).
 *   (b) Extração semântica (Python): interpreta o TEXTO de cada nó captado.
 *   (c) Classificador/correlação (Python): cruza (a) + (b) e decide.
 *
 * O que conta como "estrutural/sintático" aqui (permitido neste arquivo):
 *   - tipo de mutação (inserção nova x substituição de nó existente)
 *   - formato de valor monetário (regex de dígitos, não nome da cobrança)
 *   - formato de relógio mm:ss (regex de dígitos, não a palavra "restam")
 *   - checkbox pré-marcado (atributo, não rótulo)
 *   - saliência visual (opacidade/contraste/fonte) de elementos clicáveis
 *
 * O que NÃO entra aqui (fica para o módulo semântico em Python):
 *   - qualquer palavra-chave de urgência, cobrança ou retenção
 *   - qualquer julgamento de "isso é ou não é dark pattern"
 */
import { JSDOM } from "jsdom";
import * as fs from "fs";
import * as path from "path";

const PASTA_PAGINAS = path.resolve(__dirname, "../../paginas");
const PASTA_SAIDA = path.resolve(__dirname, "../../resultados/sinais_estruturais");
const TEMPO_ESPERA_MS = 3500;

const TAGS_IGNORADAS = new Set(["SCRIPT", "STYLE", "HEAD", "TITLE", "META", "LINK", "NOSCRIPT"]);

type TipoEvento =
  | "insercao_nova"
  | "substituicao_elemento"
  | "elemento_presente_no_carregamento";

type PadraoDetectado =
  | "valor_monetario"
  | "formato_temporal"
  | "baixa_saliencia_visual"
  | "checkbox_pre_marcado";

type EstiloComputado = {
  opacidade: number;
  fontSizePx: number;
  contraste: number | null;
};

type ElementoCaptado = {
  idElemento: string;
  tag: string;
  texto: string;
  textoContexto: string;
  tipoEvento: TipoEvento;
  padroesDetectados: PadraoDetectado[];
  estiloComputado: EstiloComputado | null;
};

type ResultadoPagina = {
  pagina: string;
  elementosCaptados: ElementoCaptado[];
};

function ehIgnoravel(el: Element): boolean {
  return TAGS_IGNORADAS.has(el.tagName);
}

function textoProprio(el: Element): string {
  return (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 160);
}

/**
 * Texto completo do elemento PAI (não do próprio nó). Existe porque
 * marcações reais frequentemente separam um dado sintático (ex.: os
 * dígitos "02:00") do texto que dá contexto a ele (ex.: "Restam...
 * para garantir este preço!") em nós DOM diferentes — o pai carrega
 * o texto combinado, o filho carrega só o dado. Continua sendo um
 * critério estrutural (distância na árvore DOM), não uma leitura de
 * significado — a interpretação do que esse texto quer dizer continua
 * sendo trabalho exclusivo do módulo semântico em Python.
 */
function textoContextoPai(el: Element): string {
  const pai = el.parentElement;
  if (!pai) return "";
  return (pai.textContent || "").trim().replace(/\s+/g, " ").slice(0, 220);
}

function parseRgba(cor: string): [number, number, number, number] | null {
  const m = cor.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)/i);
  if (!m) return null;
  const alpha = m[4] !== undefined ? Number(m[4]) : 1;
  return [Number(m[1]), Number(m[2]), Number(m[3]), alpha];
}

function luminancia([r, g, b]: [number, number, number]): number {
  const canal = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b);
}

/**
 * Cor de fundo EFETIVA de um elemento: se o próprio elemento é
 * transparente (alpha ~0, o caso comum de <span> sem background-color
 * próprio), sobe a árvore de ancestrais até achar um fundo opaco real,
 * em vez de assumir preto (bug: rgba(0,0,0,0) lido como "fundo preto"
 * por ignorar o canal alpha) ou assumir branco direto sem checar o pai
 * (bug: ignora fundo colorido de um container pai, ex.: texto branco
 * sobre fundo vermelho de um selo de alerta).
 */
function corFundoEfetiva(el: Element, window: any): [number, number, number] {
  let atual: Element | null = el;
  while (atual) {
    const estilo = window.getComputedStyle(atual);
    const rgba = parseRgba(estilo.backgroundColor || "");
    if (rgba && rgba[3] > 0.05) return [rgba[0], rgba[1], rgba[2]];
    atual = atual.parentElement;
  }
  return [255, 255, 255]; // fallback final: fundo da página (branco no nosso CSS)
}

function razaoContraste(corTexto: string, corFundoRgb: [number, number, number]): number | null {
  const rgbTexto = parseRgba(corTexto);
  if (!rgbTexto) return null;
  const l1 = luminancia([rgbTexto[0], rgbTexto[1], rgbTexto[2]]) + 0.05;
  const l2 = luminancia(corFundoRgb) + 0.05;
  return l1 > l2 ? l1 / l2 : l2 / l1;
}

function capturarEstilo(el: Element, window: any): EstiloComputado {
  const estilo = window.getComputedStyle(el);
  const opacidade = parseFloat(estilo.opacity || "1");
  const fontSizePx = parseFloat(estilo.fontSize || "16");
  const fundoEfetivo = corFundoEfetiva(el, window);
  const contraste = razaoContraste(estilo.color, fundoEfetivo);
  return { opacidade, fontSizePx, contraste };
}

function detectarPadroes(el: Element, texto: string, estilo: EstiloComputado | null): PadraoDetectado[] {
  const padroes: PadraoDetectado[] = [];

  // Formato de valor monetário: puramente sintático (dígitos + símbolo),
  // não avalia o NOME da cobrança — isso é trabalho do módulo semântico.
  if (/R\$\s?\d/.test(texto)) padroes.push("valor_monetario");

  // Formato de relógio mm:ss: puramente sintático (dígitos), não avalia
  // se há linguagem de urgência ao redor — isso também é semântico.
  if (/\d{2}:\d{2}/.test(texto)) padroes.push("formato_temporal");

  if (el.tagName === "INPUT" && (el as HTMLInputElement).type === "checkbox") {
    if ((el as HTMLInputElement).defaultChecked) padroes.push("checkbox_pre_marcado");
  }

  // "Clicável" aqui é um critério estrutural, não semântico: tags
  // nativamente interativas, OU qualquer elemento com onclick inline,
  // OU qualquer elemento com id (convenção de que só se dá id a algo
  // que será referenciado/manipulado via JS — inclusive o padrão comum
  // em dark patterns reais de usar <span>/<div> em vez de <a>/<button>
  // exatamente para evitar semântica de acessibilidade).
  const ehClicavel =
    ["A", "BUTTON"].includes(el.tagName) || el.hasAttribute("onclick") || el.id !== "";
  if (ehClicavel && estilo) {
    const baixaOpacidade = estilo.opacidade < 0.4;
    const fonteMuitoPequena = estilo.fontSizePx > 0 && estilo.fontSizePx < 11;
    const baixoContraste = estilo.contraste !== null && estilo.contraste < 2.5;
    if (baixaOpacidade || fonteMuitoPequena || baixoContraste) {
      padroes.push("baixa_saliencia_visual");
    }
  }

  return padroes;
}

async function analisarPagina(caminhoArquivo: string): Promise<ResultadoPagina> {
  const nomePagina = path.basename(caminhoArquivo, ".html");
  const eventosMutacao: { el: Element; tipoEvento: TipoEvento }[] = [];

  const dom = await JSDOM.fromFile(caminhoArquivo, {
    runScripts: "dangerously",
    resources: "usable",
    pretendToBeVisual: true,
    beforeParse(window: any) {
      const observer = new window.MutationObserver((mutations: any[]) => {
        for (const m of mutations) {
          if (m.type !== "childList") continue;
          const houveRemocao = m.removedNodes.length > 0;
          m.addedNodes.forEach((node: any) => {
            if (node.nodeType !== 1) return; // só elementos, não texto solto
            const el = node as Element;
            if (ehIgnoravel(el)) return;
            // replaceWith() dispara um único registro de mutação com
            // removedNodes E addedNodes juntos -> substituição de nó que
            // já existia (ex.: placeholder "calculando..." sendo resolvido).
            // Uma mutação só com addedNodes -> inserção genuinamente nova,
            // sem nó anterior correspondente (ex.: taxa surgindo do nada).
            eventosMutacao.push({
              el,
              tipoEvento: houveRemocao ? "substituicao_elemento" : "insercao_nova",
            });
          });
        }
      });
      window.document.addEventListener("DOMContentLoaded", () => {
        observer.observe(window.document.body, { childList: true, subtree: true });
      });
    },
  });

  await new Promise((resolve) => setTimeout(resolve, TEMPO_ESPERA_MS));

  const { window } = dom;
  const { document } = window;
  const elementosCaptados: ElementoCaptado[] = [];
  const idsJaCaptadosPorMutacao = new Set<Element>();

  // 1) Eventos de mutação (dinâmicos)
  for (const { el, tipoEvento } of eventosMutacao) {
    const texto = textoProprio(el);
    const estilo = capturarEstilo(el, window as any);
    const padroes = detectarPadroes(el, texto, estilo);
    elementosCaptados.push({
      idElemento: el.id || "(sem id)",
      tag: el.tagName.toLowerCase(),
      texto,
      textoContexto: textoContextoPai(el),
      tipoEvento,
      padroesDetectados: padroes,
      estiloComputado: estilo,
    });
    idsJaCaptadosPorMutacao.add(el);
  }

  // 2) Elementos estáticos (presentes desde o carregamento) — varredura
  // limitada a nós-folha (sem filhos-elemento) para não duplicar em
  // ancestrais, e só reportados se baterem algum padrão sintático/estrutural
  // (não é filtro de vocabulário: é filtro de "isso carrega um dado
  // estruturalmente relevante" — formato monetário/temporal, é clicável
  // com baixa saliência, ou é checkbox pré-marcado).
  document.querySelectorAll("*").forEach((el: Element) => {
    if (ehIgnoravel(el)) return;
    if (idsJaCaptadosPorMutacao.has(el)) return;
    if (el.children.length > 0 && el.tagName !== "INPUT") return; // só folhas

    const texto = textoProprio(el);
    const estilo = capturarEstilo(el, window as any);
    const padroes = detectarPadroes(el, texto, estilo);
    if (padroes.length === 0) return; // nada estruturalmente notável

    elementosCaptados.push({
      idElemento: el.id || "(sem id)",
      tag: el.tagName.toLowerCase(),
      texto,
      textoContexto: textoContextoPai(el),
      tipoEvento: "elemento_presente_no_carregamento",
      padroesDetectados: padroes,
      estiloComputado: estilo,
    });
  });

  window.close();
  return { pagina: nomePagina, elementosCaptados };
}

async function main() {
  if (!fs.existsSync(PASTA_SAIDA)) fs.mkdirSync(PASTA_SAIDA, { recursive: true });
  const arquivos = fs.readdirSync(PASTA_PAGINAS).filter((f) => f.endsWith(".html"));
  console.log(`Encontradas ${arquivos.length} páginas em ${PASTA_PAGINAS}`);

  for (const arquivo of arquivos) {
    const caminho = path.join(PASTA_PAGINAS, arquivo);
    console.log(`Analisando ${arquivo}...`);
    const resultado = await analisarPagina(caminho);
    const saida = path.join(PASTA_SAIDA, `${resultado.pagina}.json`);
    fs.writeFileSync(saida, JSON.stringify(resultado, null, 2), "utf-8");
    console.log(`  -> ${resultado.elementosCaptados.length} elemento(s) captado(s) pelo sensor`);
  }
  console.log(`\nJSONs salvos em ${PASTA_SAIDA}`);
}

main().catch((err) => {
  console.error("Erro no sensor estrutural:", err);
  process.exit(1);
});
