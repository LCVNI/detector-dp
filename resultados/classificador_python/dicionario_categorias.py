"""
Dicionário de palavras-chave por categoria de Dark Pattern.

Regra R2 do plano do grupo: o vocabulário usado aqui para DETECTAR não pode
ser idêntico ao vocabulário usado para GERAR variações sintéticas (Etapa 1.5).
Por isso as listas abaixo são por radical/tema (ex.: "process", "manuse")
em vez de frases inteiras copiadas do HTML das páginas-base — se as duas
listas fossem idênticas, o resultado de Precisão/Recall não teria valor
probatório, só mostraria o gerador e o detector concordando consigo mesmos.

Cada entrada é um radical (substring, case-insensitive) — não uma palavra
inteira — para pegar variações de flexão (ex.: "process" pega "processamento",
"processar", "processo").
"""

# Furtividade: nomes vagos/genéricos de cobrança, linguagem de ocultação
FURTIVIDADE_SUSPEITO = [
    "taxa de conveni", "ajuste de process", "process", "manuse",
    "custo adicional", "custo extra", "cobrança automát",
    "renovação automát", "renova automat", "tarifa de serviç",
    "encargo", "acréscimo",
]

# Contraprova de Furtividade: nomes de cobrança padrão/esperados em
# e-commerce, que NÃO devem, sozinhos, contar como furtividade — é
# exatamente o caso de controle_mutacao.html (frete calculado à parte).
FURTIVIDADE_LEGITIMO = [
    "frete", "entrega", "envio", "imposto", "icms", "parcelamento",
    "juros informados", "seguro (opcional)",
]

# Ação Forçada: urgência artificial + consentimento empurrado
ACAO_FORCADA_SUSPEITO = [
    "restam", "última", "últimas unidades", "apenas hoje", "só hoje",
    "garantir este preço", "estoque limitado", "corra", "não perca",
    "oferta expira", "por tempo limitado", "quero receber ofertas",
    "parceiros selecionados", "assinar automaticamente",
]

# Obstrução: linguagem de retenção usada para dificultar o cancelamento
OBSTRUCAO_SUSPEITO = [
    "cancelar", "encerrar assinatura", "tem certeza", "você vai perder",
    "perderá acesso", "pausar assinatura", "confirmação final",
    "cancelamento é imediato",
]
