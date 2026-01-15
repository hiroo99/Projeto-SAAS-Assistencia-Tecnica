import os
import re
from dotenv import load_dotenv
from mistralai.client import MistralClient

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))


def gerar_resumo(problema_relatado: str) -> str:
    """
    Gera um resumo conciso do problema relatado pelo cliente.
    """
    try:
        prompt = (
            f"Resuma o seguinte problema relatado de forma concisa e "
            f"técnica, focando nos pontos principais: {problema_relatado}"
        )
        response = client.chat(
            model="mistral-large-latest", messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erro ao gerar resumo: {e}")
        return "Resumo não disponível."


def gerar_pre_diagnostico(
    tipo_aparelho: str, marca_modelo: str, problema_relatado: str
) -> str:
    """
    Gera um pré-diagnóstico baseado nas informações do aparelho e problema.
    """
    try:
        prompt = (
            "Act as a senior computer and smartphone repair technician, focused on fast bench-level diagnosis.\n\n"
            "Service context:\n"
            f"- Device: {tipo_aparelho} {marca_modelo}\n"
            f"- Reported issue: {problema_relatado}\n\n"
            "Mandatory rules:\n"
            "- DO NOT repeat the reported issue.\n"
            "- DO NOT rewrite or summarize the context.\n"
            "- Write in plain text only (no lists, no markdown, no symbols).\n"
            "- Start by stating the main suspected cause.\n"
            "- Use extremely concise, technical language.\n"
            "- Limit the entire response to a maximum of 60 words.\n"
            "- Avoid explanations, background, or theory.\n\n"
            "Response language:\n"
            "- The entire response MUST be written in Brazilian Portuguese.\n\n"
            "Mandatory response format:\n"
            "Paragraph 1: One short sentence stating the most likely cause.\n\n"
            "Paragraph 2: One short sentence stating the first diagnostic check.\n\n"
            "Insert exactly one blank line between paragraphs.\n\n"
            "End with exactly:\n\n"
            "Suspeitos principais:\n"
            "1) <causa> – Testar: <teste direto>\n"
            "2) <causa> – Testar: <teste direto>\n\n"
            "Goal:\n"
            "Deliver a minimal, actionable diagnosis for an experienced repair technician."
        )
        response = client.chat(
            model="mistral-large-latest", messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erro ao gerar pré-diagnóstico: {e}")
        return "Pré-diagnóstico não disponível."


def filtrar_dados_relevantes(consulta: str, dados_contexto: dict) -> dict:
    """
    Filtra dados de contexto baseados em keywords da consulta para reduzir tokens.
    Retorna apenas dados relevantes (máx 15 itens por categoria).
    """
    consulta_lower = consulta.lower()
    dados_filtrados = {"clientes": [], "os": [], "produtos": [], "financeiro": {}}

    # Keywords para cada tipo (expandidos com sinônimos)
    keywords_clientes = [
        "cliente",
        "clientes",
        "pessoa",
        "nome",
        "telefone",
        "email",
        "contato",
        "usuário",
        "cadastro",
    ]
    keywords_os = [
        "os",
        "ordem",
        "servico",
        "serviços",
        "reparo",
        "status",
        "aparelho",
        "ordem de serviço",
        "reparação",
        "manutenção",
        "aberta",
        "fechada",
        "em reparo",
        "entregue",
        "cancelada",
    ]
    keywords_produtos = [
        "produto",
        "produtos",
        "estoque",
        "inventario",
        "peca",
        "peças",
        "inventário",
        "material",
        "componente",
    ]
    keywords_financeiro = [
        "receita",
        "faturamento",
        "venda",
        "financeiro",
        "valor",
        "dinheiro",
        "lucro",
        "custo",
        "pagamento",
        "cobrança",
    ]

    # Verificar se consulta menciona clientes
    if any(kw in consulta_lower for kw in keywords_clientes):
        dados_filtrados["clientes"] = dados_contexto.get("clientes", [])[:15]
        # Se menciona cliente específico, incluir OS relacionadas
        if "os" in consulta_lower or "ordem" in consulta_lower:
            dados_filtrados["os"] = dados_contexto.get("os", [])[:10]

    # Verificar se consulta menciona OS
    if any(kw in consulta_lower for kw in keywords_os):
        dados_filtrados["os"] = dados_contexto.get("os", [])[:15]

    # Verificar se consulta menciona produtos
    if any(kw in consulta_lower for kw in keywords_produtos):
        dados_filtrados["produtos"] = dados_contexto.get("produtos", [])[:15]

    # Verificar se consulta menciona financeiro
    if any(kw in consulta_lower for kw in keywords_financeiro):
        dados_filtrados["financeiro"] = {
            "receitas_totais": dados_contexto.get("receitas_totais", 0),
            "os_entregues": dados_contexto.get("os_entregues", 0),
            "total_os": dados_contexto.get("total_os", 0),
            "total_clientes": dados_contexto.get("total_clientes", 0),
        }

    # Se nenhuma categoria específica, incluir resumo básico
    if not any(dados_filtrados.values()):
        dados_filtrados["clientes"] = dados_contexto.get("clientes", [])[:5]
        dados_filtrados["os"] = dados_contexto.get("os", [])[:5]
        dados_filtrados["produtos"] = dados_contexto.get("produtos", [])[:5]
        dados_filtrados["financeiro"] = {
            "receitas_totais": dados_contexto.get("receitas_totais", 0),
            "total_os": dados_contexto.get("total_os", 0),
            "total_clientes": dados_contexto.get("total_clientes", 0),
        }

    return dados_filtrados


def construir_contexto_otimizado(dados_filtrados: dict, consulta: str) -> str:
    """
    Constrói contexto conciso para o prompt, focando em dados relevantes.
    """
    contexto_parts = []

    if dados_filtrados.get("clientes"):
        clientes_str = "CLIENTES: " + ", ".join(
            [f"{c['nome']} ({c['telefone']})" for c in dados_filtrados["clientes"]]
        )
        contexto_parts.append(clientes_str)

    if dados_filtrados.get("os"):
        os_str = "ORDENS SERVIÇO: " + ", ".join(
            [
                f"{os['numeroOS']} - {os['clienteNome']} - {os['status']}"
                for os in dados_filtrados["os"]
            ]
        )
        contexto_parts.append(os_str)

    if dados_filtrados.get("produtos"):
        produtos_str = "PRODUTOS: " + ", ".join(
            [
                f"{p['nome']} (Qtd: {p['quantidade']})"
                for p in dados_filtrados["produtos"]
            ]
        )
        contexto_parts.append(produtos_str)

    if dados_filtrados.get("financeiro"):
        fin = dados_filtrados["financeiro"]
        fin_str = f"FINANCEIRO: Receitas R$ {fin['receitas_totais']:.2f}, {fin['os_entregues']} OS entregues"
        contexto_parts.append(fin_str)

    return "\n".join(contexto_parts)


def construir_prompt_otimizado(contexto: str, consulta: str) -> str:
    """
    Constrói prompt otimizado com few-shot examples para melhor performance.
    """
    prompt = f"""
Sistema de Assistência Técnica.

DADOS DISPONÍVEIS:
{contexto}

INSTRUÇÕES:
- Interprete consultas em linguagem natural de forma inteligente
- Responda apenas com a informação solicitada, de forma concisa
- Seja direto e objetivo em português brasileiro
- Se não encontrar dados específicos, use contexto geral disponível
- Para consultas vagas, forneça resumo relevante dos dados disponíveis

EXEMPLOS:
Consulta: "Como está o João Silva?"
Resposta: João Silva, telefone (11)99999-9999, email joao@email.com

Consulta: "Status da OS 001?"
Resposta: OS #OS0001 - João Silva - Status: em_reparo

Consulta: "Quantas OS entregues?"
Resposta: 15 ordens de serviço entregues, totalizando R$ 2.500,00

Consulta: "Me mostre OS abertas"
Resposta: Ordens de serviço abertas: OS #OS0005 - Maria Santos - Status: aberta, OS #OS0007 - Pedro Lima - Status: aberta

Consulta: "Produtos em estoque baixo"
Resposta: Produtos com estoque baixo: Teclado (Qtd: 2), Mouse (Qtd: 1), Cabo USB (Qtd: 3)

Consulta: "Faturamento do mês"
Resposta: Receitas totais: R$ 15.750,00 de 23 ordens de serviço entregues

Consulta: "Cliente Maria"
Resposta: Maria Santos, telefone (11)88888-8888, email maria@email.com. Ordens relacionadas: OS #OS0005 - aberta

CONSULTA ATUAL: "{consulta}"

Responda apenas com a informação relevante:
"""
    return prompt.strip()


def interpretar_consulta_ia(consulta: str, dados_contexto: dict) -> dict:
    """
    Interpreta uma consulta em linguagem natural e extrai informações dos dados disponíveis.
    Retorna uma resposta estruturada com a informação solicitada.
    Versão otimizada com filtragem prévia e prompt conciso.
    """
    try:
        # Filtrar dados relevantes baseado na consulta
        dados_filtrados = filtrar_dados_relevantes(consulta, dados_contexto)

        # Contexto otimizado e conciso
        contexto = construir_contexto_otimizado(dados_filtrados, consulta)

        # Prompt com few-shot examples
        prompt = construir_prompt_otimizado(contexto, consulta)

        # Logging de tokens (opcional)
        tokens_inicio = len(prompt.split())  # Aproximação simples

        response = client.chat(
            model="mistral-large-latest", messages=[{"role": "user", "content": prompt}]
        )

        resposta_ia = response.choices[0].message.content.strip()

        # Logging de uso (opcional)
        tokens_fim = len(resposta_ia.split())
        print(
            f"[AI LOG] Consulta: '{consulta[:50]}...' | Tokens prompt: ~{tokens_inicio} | Tokens resposta: ~{tokens_fim}"
        )

        # Buscar dados específicos baseados na interpretação da IA
        dados_resposta = extrair_dados_consulta(consulta, dados_contexto)

        return {"resposta": resposta_ia, "dados": dados_resposta, "consulta": consulta}

    except Exception as e:
        print(f"Erro ao interpretar consulta IA: {e}")
        return {
            "resposta": "Desculpe, não foi possível processar sua consulta no momento.",
            "dados": {},
            "consulta": consulta,
        }


def extrair_dados_consulta(consulta: str, dados_contexto: dict) -> dict:
    """
    Extrai dados específicos baseados na consulta do usuário.
    """
    consulta_lower = consulta.lower()

    # Buscar por número de OS (ex: "OS005", "#OS001", "ordem 5", "serviço 001")
    os_match = re.search(
        r"(?:os|ordem|servi[çc]o)\s*(?:de\s*)?(?:servi[çc]o\s*)?(\d+)|#(?:os|OS)(\d+)",
        consulta_lower,
        re.IGNORECASE,
    )
    if os_match:
        numero = os_match.group(1) or os_match.group(2)
        numero_formatado = f"#OS{int(numero):04d}"

        for ordem in dados_contexto.get("os", []):
            if ordem["numeroOS"] == numero_formatado:
                return {"tipo": "os", "dados": ordem}

    # Buscar por nome de cliente (correspondência parcial e insensível a maiúsculas)
    for cliente in dados_contexto.get("clientes", []):
        nome_cliente_lower = cliente["nome"].lower()
        if any(
            palavra.strip().lower() in nome_cliente_lower
            or palavra.strip().lower() in consulta_lower
            for palavra in consulta_lower.split()
            if len(palavra.strip()) > 2
        ):
            # Verificar se pelo menos uma palavra da consulta está no nome ou vice-versa
            palavras_consulta = set(
                p.lower() for p in consulta_lower.split() if len(p) > 2
            )
            palavras_nome = set(
                p.lower() for p in nome_cliente_lower.split() if len(p) > 2
            )
            if palavras_consulta & palavras_nome or any(
                p in nome_cliente_lower for p in palavras_consulta
            ):
                # Buscar OS do cliente
                os_cliente = [
                    ordem
                    for ordem in dados_contexto.get("os", [])
                    if ordem["clienteId"] == cliente["id"]
                ]
                return {
                    "tipo": "cliente",
                    "dados": cliente,
                    "os_relacionadas": os_cliente,
                }

    # Consultas de status de OS (ex: "OS abertas", "ordens em reparo")
    status_keywords = {
        "aberta": ["aberta", "abertas", "pendente", "pendentes"],
        "em_reparo": ["em reparo", "reparando", "consertando", "manutenção"],
        "entregue": [
            "entregue",
            "entregues",
            "finalizada",
            "finalizadas",
            "concluída",
            "concluídas",
        ],
        "cancelada": ["cancelada", "canceladas", "cancelamento"],
    }
    for status, keywords in status_keywords.items():
        if any(kw in consulta_lower for kw in keywords) and any(
            os_kw in consulta_lower
            for os_kw in ["os", "ordem", "serviço", "ordens", "serviços"]
        ):
            os_filtradas = [
                os for os in dados_contexto.get("os", []) if os["status"] == status
            ]
            return {
                "tipo": "status_os",
                "dados": {"status": status, "ordens": os_filtradas[:10]},
            }

    # Consultas financeiras (expandido)
    if any(
        palavra in consulta_lower
        for palavra in [
            "receita",
            "faturamento",
            "venda",
            "financeiro",
            "lucro",
            "custo",
            "pagamento",
            "cobrança",
            "valor",
            "dinheiro",
        ]
    ):
        return {
            "tipo": "financeiro",
            "dados": {
                "receitas_totais": dados_contexto.get("receitas_totais", 0),
                "os_entregues": dados_contexto.get("os_entregues", 0),
                "total_os": dados_contexto.get("total_os", 0),
                "total_clientes": dados_contexto.get("total_clientes", 0),
            },
        }

    # Consultas de produtos/estoque (expandido)
    if any(
        palavra in consulta_lower
        for palavra in [
            "produto",
            "estoque",
            "inventario",
            "inventário",
            "peca",
            "peça",
            "material",
            "componente",
            "baixo",
            "baixo estoque",
        ]
    ):
        produtos_baixo_estoque = [
            p
            for p in dados_contexto.get("produtos", [])
            if p["quantidade"] < p["estoqueMinimo"]
        ]
        return {
            "tipo": "produtos",
            "dados": {
                "total_produtos": len(dados_contexto.get("produtos", [])),
                "baixo_estoque": produtos_baixo_estoque,
                "todos_produtos": dados_contexto.get("produtos", [])[
                    :20
                ],  # Limitar para não sobrecarregar
            },
        }

    return {"tipo": "nao_encontrado", "dados": {}}
