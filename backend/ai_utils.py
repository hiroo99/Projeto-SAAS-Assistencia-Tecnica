import os
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


def interpretar_consulta_ia(consulta: str, dados_contexto: dict) -> dict:
    """
    Interpreta uma consulta em linguagem natural e extrai informações dos dados disponíveis.
    Retorna uma resposta estruturada com a informação solicitada.
    """
    try:
        # Contexto dos dados disponíveis
        contexto = f"""
Sistema de Assistência Técnica - Dados Disponíveis:

CLIENTES:
Total: {dados_contexto.get('total_clientes', 0)} clientes
Lista: {', '.join([f"{c['nome']} (ID: {c['id']})" for c in dados_contexto.get('clientes', [])[:10]])}

ORDENS DE SERVIÇO:
Total: {dados_contexto.get('total_os', 0)} OS
Status disponíveis: aguardando, em_reparo, pronto, entregue, cancelado
Exemplos: {', '.join([f"{os['numeroOS']} - {os['clienteNome']} - {os['status']}" for os in dados_contexto.get('os', [])[:10]])}

PRODUTOS/ESTOQUE:
Total: {dados_contexto.get('total_produtos', 0)} produtos
Produtos com estoque baixo: {len([p for p in dados_contexto.get('produtos', []) if p['quantidade'] < p['estoqueMinimo']])} itens

FINANCEIRO:
Receitas totais: R$ {dados_contexto.get('receitas_totais', 0):.2f}
OS entregues: {dados_contexto.get('os_entregues', 0)}

CONSULTA DO USUÁRIO: "{consulta}"

INSTRUÇÕES:
1. Identifique o tipo de informação solicitada (cliente, OS, produto, financeiro, etc.)
2. Busque os dados relevantes no contexto fornecido
3. Responda de forma direta e objetiva em português brasileiro
4. Se não encontrar os dados, diga claramente que não encontrou
5. Formate a resposta de forma clara e estruturada

TIPO DE RESPOSTAS ESPERADAS:
- Para cliente específico: nome, telefone, email, endereco
- Para OS específica: numero, cliente, status, valor, aparelho, problema
- Para financeiro: valores, quantidades, períodos
- Para produtos: nome, quantidade, preço, categoria
"""

        prompt = f"""{contexto}

Sua tarefa é interpretar a consulta do usuário e fornecer a informação solicitada baseada apenas nos dados fornecidos acima.

Responda APENAS com a informação solicitada, sem introduções ou explicações adicionais.
Se a informação não estiver disponível, diga "Não encontrei essa informação nos dados disponíveis."

Formate a resposta de forma natural e conversacional, mas precisa."""

        response = client.chat(
            model="mistral-large-latest", messages=[{"role": "user", "content": prompt}]
        )

        resposta_ia = response.choices[0].message.content.strip()

        # Buscar dados específicos baseados na interpretação da IA
        dados_resposta = extrair_dados_consulta(consulta, dados_contexto)

        return {
            "resposta": resposta_ia,
            "dados": dados_resposta,
            "consulta": consulta
        }

    except Exception as e:
        print(f"Erro ao interpretar consulta IA: {e}")
        return {
            "resposta": "Desculpe, não foi possível processar sua consulta no momento.",
            "dados": {},
            "consulta": consulta
        }


def extrair_dados_consulta(consulta: str, dados_contexto: dict) -> dict:
    """
    Extrai dados específicos baseados na consulta do usuário.
    """
    consulta_lower = consulta.lower()

    # Buscar por número de OS (ex: "OS005", "#OS001")
    import re
    os_match = re.search(r'os\s*(\d+)|#os(\d+)', consulta_lower)
    if os_match:
        numero = os_match.group(1) or os_match.group(2)
        numero_formatado = f"#OS{int(numero):04d}"

        for os in dados_contexto.get('os', []):
            if os['numeroOS'] == numero_formatado:
                return {
                    "tipo": "os",
                    "dados": os
                }

    # Buscar por nome de cliente
    for cliente in dados_contexto.get('clientes', []):
        if cliente['nome'].lower() in consulta_lower:
            # Buscar OS do cliente
            os_cliente = [os for os in dados_contexto.get('os', []) if os['clienteId'] == cliente['id']]
            return {
                "tipo": "cliente",
                "dados": cliente,
                "os_relacionadas": os_cliente
            }

    # Consultas financeiras
    if any(palavra in consulta_lower for palavra in ['receita', 'faturamento', 'venda', 'financeiro']):
        return {
            "tipo": "financeiro",
            "dados": {
                "receitas_totais": dados_contexto.get('receitas_totais', 0),
                "os_entregues": dados_contexto.get('os_entregues', 0),
                "total_os": dados_contexto.get('total_os', 0),
                "total_clientes": dados_contexto.get('total_clientes', 0)
            }
        }

    # Consultas de produtos/estoque
    if any(palavra in consulta_lower for palavra in ['produto', 'estoque', 'inventario']):
        produtos_baixo_estoque = [p for p in dados_contexto.get('produtos', []) if p['quantidade'] < p['estoqueMinimo']]
        return {
            "tipo": "produtos",
            "dados": {
                "total_produtos": len(dados_contexto.get('produtos', [])),
                "baixo_estoque": produtos_baixo_estoque,
                "todos_produtos": dados_contexto.get('produtos', [])[:20]  # Limitar para não sobrecarregar
            }
        }

    return {"tipo": "nao_encontrado", "dados": {}}
