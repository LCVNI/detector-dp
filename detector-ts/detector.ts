/**
 * Detector estrutural (Etapa 2)
 * ------------------------------------------------------------
 * Abre cada página HTML de `paginas/` com jsdom (DOM + execução real
 * de JS, sem precisar baixar um binário de navegador), anexa um
 * MutationObserver ANTES da página rodar seus próprios scripts
 * (via `beforeParse`) para capturar mutações reais no DOM, espera
 * o tempo suficiente para timers como `setTimeout` dispararem, e
 * aplica heurísticas estruturais simples baseadas em:
 *   - elementos inseridos fora de uma ação do usuário (mutação)
 *   - checkboxes pré-marcados
 *   - elementos "escondidos" por baixa saliência visual (opacity,
 *     contraste de cor, fonte muito pequena) associados a uma ação
 *
 * Saída: um JSON por página em resultados/deteccao_estrutural/
 * com { pagina, elementosSuspeitos: [...], tipoDetectado: [...] }
 *
 * IMPORTANTE: o detector NÃO lê o atributo data-dp-origem. Ele é
 * usado só depois, na análise agregada (Etapa 4), nunca aqui.
 */
import { JSDOM } from "jsdom";
import * as fs from "fs";
import * as path from "path";

const PASTA_PAGINAS = path.resolve(__dirname, "../../paginas");
const PASTA_SAIDA = path.resolve(__dirname, "../../resultados/deteccao_estrutural");
const TEMPO_ESPERA_MS = 3500; // > que o maior setTimeout usado nas páginas (3000ms)

type ElementoSuspeito = {
  idElemento: string;
  tag: string;
  texto: string;
  heuristica: string;
  categoriaSugerida: "furtividade" | "obstrucao" | "acao_forcada";
};

type ResultadoPagina = {
  pagina: string;
  elementosSuspeitos: ElementoSuspeito[];
  tipoDetectado: string[];
};

function textoResumido(el: Element): string {
  return (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 120);
}

/** Parseia "rgb(r, g, b)" / "rgba(r,g,b,a)" -> [r,g,b] ou null */
function parseRgb(cor: string): [number, number, number] | null {
  const m = cor.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
  if (!m) return null;
  return [Number(m[1]), Number(m[2]), Number(m[3])];
}

/** Luminância relativa simplificada (WCAG) */
function luminancia([r, g, b]: [number, number, number]): number {
  const canal = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b);
}

function razaoContraste(corTexto: string, corFundo: string): number | null {
  const rgb1 = parseRgb(corTexto);
  const rgb2 = parseRgb(corFundo);
  if (!rgb1 || !rgb2) return null;
  const l1 = luminancia(rgb1) + 0.05;
  const l2 = luminancia(rgb2) + 0.05;
  return l1 > l2 ? l1 / l2 : l2 / l1;
}

async function analisarPagina(caminhoArquivo: string): Promise<ResultadoPagina> {
  const nomePagina = path.basename(caminhoArquivo, ".html");
  const mutacoesCapturadas: Element[] = [];

  const dom = await JSDOM.fromFile(caminhoArquivo, {
    runScripts: "dangerously",
    resources: "usable",
    pretendToBeVisual: true, // habilita timers reais e getComputedStyle utilizável
    beforeParse(window) {
      // Anexado ANTES de qualquer script da própria página rodar,
      // então captura inclusive inserções feitas via setTimeout.
      const observer = new window.MutationObserver((mutations) => {
        for (const m of mutations) {
          m.addedNodes.forEach((node) => {
            if (node.nodeType === 1) {
              mutacoesCapturadas.push(node as unknown as Element);
            }
          });
        }
      });
      window.document.addEventListener("DOMContentLoaded", () => {
        observer.observe(window.document.body, { childList: true, subtree: true });
      });
    },
  });

  // Espera os timers da própria página (ex.: taxa oculta em 3s) dispararem.
  await new Promise((resolve) => setTimeout(resolve, TEMPO_ESPERA_MS));

  const { window } = dom;
  const { document } = window;
  const elementosSuspeitos: ElementoSuspeito[] = [];

  // --- Heurística 1 (Furtividade): elemento inserido via mutação cujo
  // texto tem cara de cobrança monetária adicional ---
  for (const el of mutacoesCapturadas) {
    const texto = textoResumido(el);
    if (/R\$\s?\d/.test(texto)) {
      elementosSuspeitos.push({
        idElemento: el.id || "(sem id)",
        tag: el.tagName.toLowerCase(),
        texto,
        heuristica: "elemento com valor monetário inserido na DOM após carregamento inicial (mutação tardia)",
        categoriaSugerida: "furtividade",
      });
    }
  }

  // --- Heurística 2 (Ação Forçada): checkbox pré-marcado no HTML original ---
  document.querySelectorAll('input[type="checkbox"]').forEach((el) => {
    const input = el as HTMLInputElement;
    if (input.defaultChecked) {
      elementosSuspeitos.push({
        idElemento: input.id || "(sem id)",
        tag: "input[checkbox]",
        texto: textoResumido(input.closest("label")?.parentElement || input),
        heuristica: "checkbox vem marcado por padrão no HTML (opt-in não é escolha ativa do usuário)",
        categoriaSugerida: "acao_forcada",
      });
    }
  });

  // --- Heurística 3 (Ação Forçada): contador regressivo com linguagem de urgência ---
  // Candidatos brutos primeiro; depois mantemos só o match mais específico
  // (descartamos ancestrais cujo "acerto" é só herdado do texto de um filho).
  const candidatosTimer: Element[] = [];
  document.querySelectorAll("*").forEach((el) => {
    const texto = textoResumido(el);
    const temUrgencia = /restam|expira|últimas unidades|apenas hoje|garantir este preço/i.test(texto);
    const temFormatoTimer = /\d{2}:\d{2}/.test(texto);
    if (temUrgencia && temFormatoTimer) candidatosTimer.push(el);
  });
  const candidatosTimerEspecificos = candidatosTimer.filter(
    (el) => !candidatosTimer.some((outro) => outro !== el && el.contains(outro))
  );
  for (const el of candidatosTimerEspecificos) {
    elementosSuspeitos.push({
      idElemento: el.id || "(sem id)",
      tag: el.tagName.toLowerCase(),
      texto: textoResumido(el),
      heuristica: "texto de urgência combinado com contador em formato mm:ss",
      categoriaSugerida: "acao_forcada",
    });
  }

  // --- Heurística 4 (Obstrução): elemento clicável com baixa saliência visual
  // (contraste muito baixo, opacidade muito baixa ou fonte muito pequena)
  // associado a uma ação (texto/id sugerindo "cancelar") ---
  document.querySelectorAll('a, button, [onclick], span[id]').forEach((el) => {
    const texto = textoResumido(el).toLowerCase();
    const idOuTexto = `${el.id} ${texto}`.toLowerCase();
    const pareceAcaoSensivel = /cancelar|encerrar|excluir|remover|recusar/.test(idOuTexto);
    if (!pareceAcaoSensivel) return;

    const estilo = window.getComputedStyle(el);
    const opacidade = parseFloat(estilo.opacity || "1");
    const fontSize = parseFloat(estilo.fontSize || "16");
    const contraste = razaoContraste(estilo.color, estilo.backgroundColor || "rgb(255,255,255)");

    const baixaOpacidade = opacidade < 0.4;
    const fonteMuitoPequena = fontSize > 0 && fontSize < 11;
    const baixoContraste = contraste !== null && contraste < 2.5;

    if (baixaOpacidade || fonteMuitoPequena || baixoContraste) {
      const motivos = [
        baixaOpacidade ? `opacidade=${opacidade}` : null,
        fonteMuitoPequena ? `fonte=${fontSize}px` : null,
        baixoContraste ? `contraste≈${contraste?.toFixed(2)}:1` : null,
      ].filter(Boolean).join(", ");
      elementosSuspeitos.push({
        idElemento: el.id || "(sem id)",
        tag: el.tagName.toLowerCase(),
        texto: textoResumido(el),
        heuristica: `ação sensível com baixa saliência visual (${motivos})`,
        categoriaSugerida: "obstrucao",
      });
    }
  });

  const tipoDetectado = Array.from(new Set(elementosSuspeitos.map((e) => e.categoriaSugerida)));

  window.close();

  return { pagina: nomePagina, elementosSuspeitos, tipoDetectado };
}

async function main() {
  if (!fs.existsSync(PASTA_SAIDA)) fs.mkdirSync(PASTA_SAIDA, { recursive: true });

  const arquivos = fs
    .readdirSync(PASTA_PAGINAS)
    .filter((f) => f.endsWith(".html"));

  console.log(`Encontradas ${arquivos.length} páginas em ${PASTA_PAGINAS}`);

  for (const arquivo of arquivos) {
    const caminho = path.join(PASTA_PAGINAS, arquivo);
    console.log(`Analisando ${arquivo}...`);
    const resultado = await analisarPagina(caminho);
    const saida = path.join(PASTA_SAIDA, `${resultado.pagina}.json`);
    fs.writeFileSync(saida, JSON.stringify(resultado, null, 2), "utf-8");
    console.log(
      `  -> ${resultado.elementosSuspeitos.length} elemento(s) suspeito(s); tipos: ${
        resultado.tipoDetectado.join(", ") || "(nenhum)"
      }`
    );
  }

  console.log(`\nJSONs salvos em ${PASTA_SAIDA}`);
}

main().catch((err) => {
  console.error("Erro no detector estrutural:", err);
  process.exit(1);
});
