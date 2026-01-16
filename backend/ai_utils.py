import os
import time
from dotenv import load_dotenv
from mistralai.client import MistralClient

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

client = MistralClient(api_key=os.getenv("MISTRAL_API_KEY"))

# Cache simples em memória para dados de contexto
_cache_dados_contexto = {"dados": None, "timestamp": 0, "ttl": 300}  # 5 minutos

# Cache para resultados de IA similares
_cache_resultados_ia = {}


def get_cached_dados_contexto():
    """
    Retorna dados de contexto do cache se ainda válidos.
    """
    current_time = time.time()
    if (
        _cache_dados_contexto["dados"]
        and current_time - _cache_dados_contexto["timestamp"]
        < _cache_dados_contexto["ttl"]
    ):
        return _cache_dados_contexto["dados"]
    return None


def set_cached_dados_contexto(dados):
    """
    Armazena dados de contexto no cache.
    """
    _cache_dados_contexto["dados"] = dados
    _cache_dados_contexto["timestamp"] = time.time()


def get_cached_resultado_ia(consulta_hash):
    """
    Retorna resultado de IA do cache se existir.
    """
    return _cache_resultados_ia.get(consulta_hash)


def set_cached_resultado_ia(consulta_hash, resultado):
    """
    Armazena resultado de IA no cache (máximo 50 entradas).
    """
    if len(_cache_resultados_ia) >= 50:
        # Remove entrada mais antiga
        oldest_key = min(
            _cache_resultados_ia.keys(),
            key=lambda k: _cache_resultados_ia[k].get("timestamp", 0),
        )
        del _cache_resultados_ia[oldest_key]

    _cache_resultados_ia[consulta_hash] = {
        "resultado": resultado,
        "timestamp": time.time(),
    }


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


def interpretar_consulta_ia(
    consulta: str, dados_contexto: dict, estado_conversacional: dict = None
) -> dict:
    """
    Interpreta uma consulta em linguagem natural e extrai informações dos dados disponíveis.
    Suporta criação conversacional de dados (clientes, OS, produtos).
    Retorna uma resposta estruturada com a informação solicitada.
    """
    try:
        consulta_lower = consulta.lower()

        # Verificar se estamos em um fluxo conversacional de criação
        if estado_conversacional and estado_conversacional.get("modo"):
            return processar_fluxo_conversacional(
                consulta, estado_conversacional, dados_contexto
            )

        # Verificar se é uma pergunta conversacional (não relacionada aos dados)
        resposta_conversacional = detectar_pergunta_conversacional(consulta_lower)
        if resposta_conversacional:
            return {
                "resposta": resposta_conversacional,
                "dados": {"tipo": "conversacional"},
                "consulta": consulta,
                "estado_conversacional": None,
            }

        # Verificar se o usuário quer excluir ou editar dados
        intencao_operacao = detectar_intencao_exclusao_edicao(
            consulta_lower, dados_contexto
        )
        if intencao_operacao:
            return processar_operacao_dados(intencao_operacao, dados_contexto)

        # Verificar se o usuário quer iniciar criação de dados
        intencao_criacao = detectar_intencao_criacao(consulta_lower)
        if intencao_criacao:
            return iniciar_fluxo_criacao(intencao_criacao, dados_contexto)

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
OS entregues: {dados_contexto.get('os_entregues', 0)} OS

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

INSTRUÇÕES IMPORTANTES:
- Responda APENAS com a informação solicitada, sem introduções ou explicações adicionais
- Use APENAS texto puro, sem formatação Markdown (*, **, _, etc.) ou símbolos especiais
- Escreva de forma natural e conversacional, mas direta
- Se a informação não estiver disponível, diga "Não encontrei essa informação nos dados disponíveis."
"""

        response = client.chat(
            model="mistral-large-latest", messages=[{"role": "user", "content": prompt}]
        )

        resposta_ia = response.choices[0].message.content.strip()

        # Buscar dados específicos baseados na interpretação da IA
        dados_resposta = extrair_dados_consulta(consulta, dados_contexto)

        return {
            "resposta": resposta_ia,
            "dados": dados_resposta,
            "consulta": consulta,
            "estado_conversacional": None,  # Não há fluxo conversacional ativo
        }

    except Exception as e:
        print(f"Erro ao interpretar consulta IA: {e}")
        return {
            "resposta": "Desculpe, não foi possível processar sua consulta no momento.",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": None,
        }


def extrair_dados_consulta(consulta: str, dados_contexto: dict) -> dict:
    """
    Extrai dados específicos baseados na consulta do usuário.
    """
    consulta_lower = consulta.lower()

    # Buscar por número de OS (ex: "OS005", "#OS001")
    import re

    os_match = re.search(r"os\s*(\d+)|#os(\d+)", consulta_lower)
    if os_match:
        numero = os_match.group(1) or os_match.group(2)
        numero_formatado = f"#OS{int(numero):04d}"

        for os in dados_contexto.get("os", []):
            if os["numeroOS"] == numero_formatado:
                return {"tipo": "os", "dados": os}

    # Buscar por nome de cliente
    for cliente in dados_contexto.get("clientes", []):
        if cliente["nome"].lower() in consulta_lower:
            # Buscar OS do cliente
            os_cliente = [
                os
                for os in dados_contexto.get("os", [])
                if os["clienteId"] == cliente["id"]
            ]
            return {"tipo": "cliente", "dados": cliente, "os_relacionadas": os_cliente}

    # Consultas financeiras
    if any(
        palavra in consulta_lower
        for palavra in ["receita", "faturamento", "venda", "financeiro"]
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

    # Consultas de produtos/estoque
    if any(
        palavra in consulta_lower for palavra in ["produto", "estoque", "inventario"]
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


def detectar_intencao_criacao(consulta_lower: str) -> str:
    """
    Detecta se o usuário quer criar dados (cliente, OS, produto).
    Retorna o tipo de criação ou None.
    """
    # Padrões para detectar intenção de criação
    padroes_cliente = [
        "adicionar cliente",
        "cadastrar cliente",
        "criar cliente",
        "novo cliente",
        "registrar cliente",
        "incluir cliente",
        "quero adicionar um cliente",
        "gostaria de adicionar um cliente",
    ]

    padroes_os = [
        "criar os",
        "nova os",
        "adicionar os",
        "cadastrar os",
        "registrar os",
        "nova ordem",
        "ordem de serviço",
        "quero criar uma os",
    ]

    padroes_produto = [
        "adicionar produto",
        "cadastrar produto",
        "criar produto",
        "novo produto",
        "registrar produto",
        "incluir produto",
        "quero adicionar um produto",
    ]

    for padrao in padroes_cliente:
        if padrao in consulta_lower:
            return "cliente"

    for padrao in padroes_os:
        if padrao in consulta_lower:
            return "os"

    for padrao in padroes_produto:
        if padrao in consulta_lower:
            return "produto"

    return None


def detectar_intencao_exclusao_edicao(
    consulta_lower: str, dados_contexto: dict
) -> dict:
    """
    Detecta se o usuário quer excluir ou editar dados.
    Retorna dict com tipo de operação e entidade afetada.
    """
    import re

    # Padrões para exclusão
    padroes_exclusao = [
        "exclua",
        "delete",
        "remova",
        "apague",
        "elimine",
        "quero excluir",
        "quero deletar",
        "quero remover",
    ]

    # Padrões para edição
    padroes_edicao = [
        "altere",
        "modifique",
        "atualize",
        "edite",
        "mude",
        "alterar",
        "modificar",
        "quero alterar",
        "quero modificar",
        "quero atualizar",
        "quero editar",
    ]

    # Verificar exclusão primeiro
    for padrao in padroes_exclusao:
        if padrao in consulta_lower:
            # Tentar identificar o que excluir
            entidade = identificar_entidade_para_operacao(
                consulta_lower, dados_contexto
            )
            if entidade:
                return {
                    "operacao": "exclusao",
                    "tipo_entidade": entidade["tipo"],
                    "entidade": entidade["dados"],
                    "id": entidade["id"],
                }

    # Verificar edição
    for padrao in padroes_edicao:
        if padrao in consulta_lower:
            # Tentar identificar o que editar
            entidade = identificar_entidade_para_operacao(
                consulta_lower, dados_contexto
            )
            if entidade:
                return {
                    "operacao": "edicao",
                    "tipo_entidade": entidade["tipo"],
                    "entidade": entidade["dados"],
                    "id": entidade["id"],
                }

    return None


def identificar_entidade_para_operacao(
    consulta_lower: str, dados_contexto: dict
) -> dict:
    """
    Identifica qual entidade (cliente, OS, produto) o usuário quer operar.
    Usa busca inteligente por palavras-chave.
    """
    import re

    # Primeiro: procurar por números de OS (mais específico)
    os_match = re.search(r"os\s*(\d+)|#os(\d+)", consulta_lower)
    if os_match:
        numero = os_match.group(1) or os_match.group(2)
        numero_formatado = f"#OS{int(numero):04d}"

        for os in dados_contexto.get("os", []):
            if os["numeroOS"] == numero_formatado:
                return {"tipo": "os", "dados": os, "id": os["id"]}

    # Segundo: procurar por códigos de produto (específicos)
    for produto in dados_contexto.get("produtos", []):
        if produto["codigo"].upper() in consulta_lower.upper():
            return {"tipo": "produto", "dados": produto, "id": produto["id"]}

    # Terceiro: busca inteligente por produtos (mais flexível)
    produto_encontrado = encontrar_produto_por_nome_inteligente(
        consulta_lower, dados_contexto
    )
    if produto_encontrado:
        return produto_encontrado

    # Quarto: busca inteligente por clientes (mais flexível)
    cliente_encontrado = encontrar_cliente_por_nome_inteligente(
        consulta_lower, dados_contexto
    )
    if cliente_encontrado:
        return cliente_encontrado

    # Quinto: busca inteligente por OS (usando contexto de cliente)
    os_encontrada = encontrar_os_por_contexto_inteligente(
        consulta_lower, dados_contexto
    )
    if os_encontrada:
        return os_encontrada

    # Sexto: busca de emergência por qualquer correspondência (fallback)
    # Buscar por nomes de cliente (correspondência exata)
    for cliente in dados_contexto.get("clientes", []):
        if cliente["nome"].lower() in consulta_lower:
            return {"tipo": "cliente", "dados": cliente, "id": cliente["id"]}

    # Buscar por nomes de produto (correspondência exata)
    for produto in dados_contexto.get("produtos", []):
        if produto["nome"].lower() in consulta_lower:
            return {"tipo": "produto", "dados": produto, "id": produto["id"]}

    return None


def encontrar_produto_por_nome_inteligente(
    consulta_lower: str, dados_contexto: dict
) -> dict:
    """
    Busca inteligente por produtos usando palavras-chave.
    Retorna o produto com melhor correspondência.
    """
    return encontrar_entidade_por_nome_inteligente(
        consulta_lower, dados_contexto, "produto"
    )


def encontrar_cliente_por_nome_inteligente(
    consulta_lower: str, dados_contexto: dict
) -> dict:
    """
    Busca inteligente por clientes usando palavras-chave.
    Retorna o cliente com melhor correspondência.
    """
    return encontrar_entidade_por_nome_inteligente(
        consulta_lower, dados_contexto, "cliente"
    )


def encontrar_os_por_contexto_inteligente(
    consulta_lower: str, dados_contexto: dict
) -> dict:
    """
    Busca inteligente por OS usando contexto (cliente, número, etc.).
    Retorna a OS com melhor correspondência.
    """
    os_list = dados_contexto.get("os", [])
    if not os_list:
        return None

    # Separar palavras da consulta (remover palavras de comando)
    palavras_comando = [
        "exclua",
        "delete",
        "remova",
        "altere",
        "modifique",
        "excluir",
        "deletar",
        "remover",
        "alterar",
        "modificar",
        "o",
        "a",
        "do",
        "da",
        "de",
        "do",
        "da",
        "um",
        "uma",
        "os",
        "ordem",
        "servico",
        "serviço",
        "cliente",
    ]
    palavras_consulta = [
        palavra
        for palavra in consulta_lower.split()
        if palavra not in palavras_comando and len(palavra) > 1
    ]

    melhor_correspondencia = None
    melhor_score = 0

    for os_item in os_list:
        score = 0
        nome_cliente = (os_item.get("clienteNome") or "").lower()
        numero_os = (os_item.get("numeroOS") or "").lower()

        # Verificar cada palavra da consulta no nome do cliente
        for palavra in palavras_consulta:
            if palavra in nome_cliente:
                score += len(palavra) * 2  # Clientes têm prioridade maior
            if palavra in numero_os:
                score += len(palavra) * 3  # Números de OS têm prioridade máxima

        # Bônus se todas as palavras estão presentes no cliente
        if all(palavra in nome_cliente for palavra in palavras_consulta):
            score += 200

        # Bônus para sequência exata
        if " ".join(palavras_consulta) in nome_cliente:
            score += 100

        # Atualizar melhor correspondência
        if score > melhor_score and score >= 2:  # Mínimo de 2 pontos para OS
            melhor_score = score
            melhor_correspondencia = {
                "tipo": "os",
                "dados": os_item,
                "id": os_item["id"],
                "score": score,
            }

    return melhor_correspondencia


def encontrar_entidade_por_nome_inteligente(
    consulta_lower: str, dados_contexto: dict, tipo_entidade: str
) -> dict:
    """
    Busca inteligente genérica por entidades usando palavras-chave.
    Funciona para produtos e clientes.
    """
    if tipo_entidade == "produto":
        entidades = dados_contexto.get("produtos", [])
        campo_nome = "nome"
        campo_codigo = "codigo"
    elif tipo_entidade == "cliente":
        entidades = dados_contexto.get("clientes", [])
        campo_nome = "nome"
        campo_codigo = None
    else:
        return None

    if not entidades:
        return None

    # Separar palavras da consulta (remover palavras de comando)
    palavras_comando = [
        "exclua",
        "delete",
        "remova",
        "altere",
        "modifique",
        "excluir",
        "deletar",
        "remover",
        "alterar",
        "modificar",
        "o",
        "a",
        "do",
        "da",
        "de",
        "um",
        "uma",
        tipo_entidade,
    ]
    palavras_consulta = [
        palavra
        for palavra in consulta_lower.split()
        if palavra not in palavras_comando and len(palavra) > 2
    ]

    if not palavras_consulta:
        return None

    melhor_correspondencia = None
    melhor_score = 0

    for entidade in entidades:
        nome_entidade = entidade[campo_nome].lower()
        score = 0

        # Verificar cada palavra da consulta no nome da entidade
        for palavra in palavras_consulta:
            if palavra in nome_entidade:
                score += len(palavra)  # Palavras mais longas têm mais peso

        # Verificar código (para produtos)
        if campo_codigo and entidade.get(campo_codigo):
            codigo_entidade = entidade[campo_codigo].lower()
            for palavra in palavras_consulta:
                if palavra in codigo_entidade:
                    score += len(palavra) * 1.5  # Código tem peso menor que nome

        # Bônus se todas as palavras estão presentes
        if all(palavra in nome_entidade for palavra in palavras_consulta):
            score += 100

        # Bônus se a sequência exata está presente
        if " ".join(palavras_consulta) in nome_entidade:
            score += 50

        # Atualizar melhor correspondência
        if score > melhor_score and score >= 3:  # Mínimo de 3 pontos para considerar
            melhor_score = score
            melhor_correspondencia = {
                "tipo": tipo_entidade,
                "dados": entidade,
                "id": entidade["id"],
                "score": score,
            }

    return melhor_correspondencia


def iniciar_fluxo_criacao(tipo: str, dados_contexto: dict) -> dict:
    """
    Inicia um fluxo conversacional para criação de dados.
    """
    if tipo == "cliente":
        estado = {
            "modo": "criacao_cliente",
            "etapa": 1,
            "dados": {},
            "campos_obrigatorios": ["nome", "cpfCnpj", "telefone"],
            "campos_opcionais": ["email", "endereco", "observacoes"],
            "proximo_campo": "nome",
        }
        resposta = "Certo! Vou ajudar você a cadastrar um novo cliente. Qual o nome completo do cliente?"

    elif tipo == "os":
        estado = {
            "modo": "criacao_os",
            "etapa": 1,
            "dados": {},
            "campos_obrigatorios": [
                "clienteId",
                "tipoAparelho",
                "marcaModelo",
                "problemaRelatado",
            ],
            "campos_opcionais": [
                "imeiSerial",
                "corAparelho",
                "valorOrcamento",
                "observacoes",
            ],
            "proximo_campo": "cliente",
        }
        resposta = "Perfeito! Vou criar uma nova Ordem de Serviço. Primeiro, preciso saber qual cliente. Você pode informar o nome do cliente ou seu ID."

    elif tipo == "produto":
        estado = {
            "modo": "criacao_produto",
            "etapa": 1,
            "dados": {},
            "campos_obrigatorios": ["nome", "categoria", "codigo"],
            "campos_opcionais": [
                "descricao",
                "quantidade",
                "estoqueMinimo",
                "precoCusto",
                "precoVenda",
                "fornecedor",
                "localizacao",
            ],
            "proximo_campo": "nome",
        }
        resposta = "Excelente! Vou cadastrar um novo produto. Qual o nome do produto?"

    else:
        return {
            "resposta": "Desculpe, não entendi o tipo de dado que você quer criar.",
            "dados": {},
            "consulta": "",
            "estado_conversacional": None,
        }

    return {
        "resposta": resposta,
        "dados": {"tipo": "fluxo_criacao", "modo": estado["modo"]},
        "consulta": "",
        "estado_conversacional": estado,
    }


def processar_fluxo_conversacional(
    consulta: str, estado: dict, dados_contexto: dict
) -> dict:
    """
    Processa uma resposta dentro de um fluxo conversacional de criação.
    """
    modo = estado.get("modo")

    if modo == "criacao_cliente":
        return processar_criacao_cliente(consulta, estado, dados_contexto)
    elif modo == "criacao_os":
        return processar_criacao_os(consulta, estado, dados_contexto)
    elif modo == "criacao_produto":
        return processar_criacao_produto(consulta, estado, dados_contexto)
    elif modo.startswith("exclusao_"):
        return processar_confirmacao_exclusao(consulta, estado, dados_contexto)
    elif modo.startswith("edicao_"):
        return processar_fluxo_edicao(consulta, estado, dados_contexto)
    else:
        # Finalizar fluxo se modo desconhecido
        return {
            "resposta": "Ocorreu um erro no fluxo conversacional. Vamos recomeçar.",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": None,
        }


def processar_criacao_cliente(
    consulta: str, estado: dict, dados_contexto: dict
) -> dict:
    """
    Processa o fluxo de criação de cliente.
    """
    etapa = estado.get("etapa", 1)
    dados = estado.get("dados", {})
    campos_obrigatorios = estado.get("campos_obrigatorios", [])
    campos_opcionais = estado.get("campos_opcionais", [])

    # Verificar comandos especiais
    consulta_lower = consulta.lower().strip()
    if consulta_lower in ["cancelar", "cancela", "parar", "sair"]:
        return {
            "resposta": "Ok, cancelei o cadastro do cliente.",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": None,
        }

    # Processar conforme etapa
    if etapa == 1:  # Nome
        if not consulta.strip():
            resposta = "Por favor, informe o nome completo do cliente:"
        else:
            dados["nome"] = consulta.strip()
            estado["dados"] = dados
            estado["etapa"] = 2
            estado["proximo_campo"] = "cpfCnpj"
            resposta = "Perfeito! Agora preciso do CPF ou CNPJ do cliente:"

    elif etapa == 2:  # CPF/CNPJ
        # Validação básica de CPF/CNPJ
        cpf_limpo = consulta.replace(".", "").replace("-", "").replace("/", "").strip()
        if len(cpf_limpo) < 11:
            resposta = "CPF/CNPJ parece estar incompleto. Por favor, digite novamente:"
        elif not cpf_limpo.isdigit():
            resposta = (
                "CPF/CNPJ deve conter apenas números. Por favor, digite novamente:"
            )
        else:
            # Verificar se já existe
            cpf_existe = any(
                c["cpf_cnpj"].replace(".", "").replace("-", "").replace("/", "")
                == cpf_limpo
                for c in dados_contexto.get("clientes", [])
            )
            if cpf_existe:
                resposta = "Este CPF/CNPJ já está cadastrado no sistema. Por favor, verifique ou use outro:"
            else:
                dados["cpfCnpj"] = consulta.strip()
                estado["dados"] = dados
                estado["etapa"] = 3
                estado["proximo_campo"] = "telefone"
                resposta = "Ótimo! Agora qual o telefone de contato?"

    elif etapa == 3:  # Telefone
        telefone_limpo = (
            consulta.replace("(", "")
            .replace(")", "")
            .replace("-", "")
            .replace(" ", "")
            .strip()
        )
        if len(telefone_limpo) < 10:
            resposta = "Telefone parece estar incompleto. Por favor, digite novamente:"
        elif not telefone_limpo.isdigit():
            resposta = (
                "Telefone deve conter apenas números. Por favor, digite novamente:"
            )
        else:
            dados["telefone"] = consulta.strip()
            estado["dados"] = dados
            estado["etapa"] = 4
            estado["proximo_campo"] = "confirmacao"

            # Resumo para confirmação - formatado para melhor visualização
            resposta = f"""Excelente! Aqui está o resumo do cliente:

Nome: {dados['nome']}
CPF/CNPJ: {dados['cpfCnpj']}
Telefone: {dados['telefone']}

Deseja confirmar o cadastro ou adicionar mais informações?

Digite:
• 'sim' ou 'confirmar' para cadastrar
• 'email' para adicionar email
• 'endereco' para adicionar endereço
• 'cancelar' para desistir"""

    elif etapa == 4:  # Confirmação/Finalização
        if any(
            palavra in consulta_lower
            for palavra in [
                "sim",
                "confirmar",
                "confirme",
                "ok",
                "certo",
                "cadastrar",
                "salvar",
                "finalizar",
                "pronto",
                "pode cadastrar",
                "cadastra",
            ]
        ):
            # Tentar criar o cliente
            try:
                # Preparar dados de criação incluindo campos opcionais
                dados_criacao = {
                    "nome": dados["nome"],
                    "cpfCnpj": dados["cpfCnpj"],
                    "telefone": dados["telefone"],
                    "status": "ativo",
                }

                # Adicionar campos opcionais se foram fornecidos
                if "email" in dados and dados["email"]:
                    dados_criacao["email"] = dados["email"]
                if "endereco" in dados and dados["endereco"]:
                    dados_criacao["endereco"] = dados["endereco"]
                if "observacoes" in dados and dados["observacoes"]:
                    dados_criacao["observacoes"] = dados["observacoes"]

                return {
                    "resposta": f"✅ Cliente '{dados['nome']}' cadastrado com sucesso!",
                    "dados": {"tipo": "cliente_criado", "dados": dados_criacao},
                    "consulta": consulta,
                    "estado_conversacional": None,
                    "acao": {"tipo": "criar_cliente", "dados": dados_criacao},
                }
            except Exception as e:
                return {
                    "resposta": f"❌ Ocorreu um erro ao cadastrar o cliente: {str(e)}",
                    "dados": {},
                    "consulta": consulta,
                    "estado_conversacional": estado,  # Manter estado para tentar novamente
                }

        elif any(
            palavra in consulta_lower for palavra in ["email", "endereco", "mais"]
        ):
            estado["etapa"] = 5
            resposta = "Certo! Qual informação adicional você quer adicionar? (email, endereço ou observações)"

        else:
            resposta = """Não entendi o comando. Por favor, escolha uma das opções:

• 'sim', 'confirmar' ou 'confirme' para cadastrar o cliente
• 'email' para adicionar email
• 'endereco' para adicionar endereço
• 'cancelar' para desistir"""

    elif etapa == 5:  # Campos opcionais
        if "email" in consulta_lower:
            estado["etapa"] = 6
            resposta = "Qual o endereço de email do cliente?"
        elif "endereco" in consulta_lower or "endereço" in consulta_lower:
            estado["etapa"] = 7
            resposta = "Qual o endereço completo do cliente?"
        elif "observacoes" in consulta_lower or "observações" in consulta_lower:
            estado["etapa"] = 8
            resposta = "Quais as observações sobre o cliente?"
        else:
            resposta = "Por favor, escolha: email, endereço ou observações:"

    elif etapa == 6:  # Email
        dados["email"] = consulta.strip()
        estado["dados"] = dados
        estado["etapa"] = 4  # Volta para confirmação
        resposta = f"""Email adicionado! Aqui está o resumo atualizado:

Nome: {dados['nome']}
CPF/CNPJ: {dados['cpfCnpj']}
Telefone: {dados['telefone']}
Email: {dados['email']}

Deseja confirmar o cadastro ou adicionar mais informações?

Digite:
• 'sim' ou 'confirmar' para cadastrar
• 'endereco' para adicionar endereço
• 'cancelar' para desistir"""

    elif etapa == 7:  # Endereço
        dados["endereco"] = consulta.strip()
        estado["dados"] = dados
        estado["etapa"] = 4  # Volta para confirmação
        resposta = f"""Endereço adicionado! Aqui está o resumo atualizado:

Nome: {dados['nome']}
CPF/CNPJ: {dados['cpfCnpj']}
Telefone: {dados['telefone']}
Endereço: {dados['endereco']}

Deseja confirmar o cadastro ou adicionar mais informações?

Digite:
• 'sim' ou 'confirmar' para cadastrar
• 'email' para adicionar email
• 'cancelar' para desistir"""

    elif etapa == 8:  # Observações
        dados["observacoes"] = consulta.strip()
        estado["dados"] = dados
        estado["etapa"] = 4  # Volta para confirmação
        resposta = f"""Observações adicionadas! Aqui está o resumo atualizado:

Nome: {dados['nome']}
CPF/CNPJ: {dados['cpfCnpj']}
Telefone: {dados['telefone']}
Observações: {dados['observacoes']}

Deseja confirmar o cadastro ou adicionar mais informações?

Digite:
• 'sim' ou 'confirmar' para cadastrar
• 'cancelar' para desistir"""

    else:
        resposta = "Ocorreu um erro no fluxo. Vamos recomeçar."

    return {
        "resposta": resposta,
        "dados": {"tipo": "fluxo_continuacao"},
        "consulta": consulta,
        "estado_conversacional": estado,
    }


def processar_criacao_os(consulta: str, estado: dict, dados_contexto: dict) -> dict:
    """
    Processa o fluxo de criação de OS (placeholder para implementação futura).
    """
    return {
        "resposta": "Funcionalidade de criação de OS ainda em desenvolvimento. Por enquanto, use o formulário normal.",
        "dados": {},
        "consulta": consulta,
        "estado_conversacional": None,
    }


def processar_criacao_produto(
    consulta: str, estado: dict, dados_contexto: dict
) -> dict:
    """
    Processa o fluxo de criação de produto (placeholder para implementação futura).
    """
    return {
        "resposta": "Funcionalidade de criação de produto ainda em desenvolvimento. Por enquanto, use o formulário normal.",
        "dados": {},
        "consulta": consulta,
        "estado_conversacional": None,
    }


def processar_operacao_dados(intencao: dict, dados_contexto: dict) -> dict:
    """
    Processa operações de exclusão ou edição de dados.
    """
    operacao = intencao.get("operacao")
    tipo_entidade = intencao.get("tipo_entidade")
    entidade = intencao.get("entidade")
    entidade_id = intencao.get("id")

    if operacao == "exclusao":
        return processar_exclusao_dados(tipo_entidade, entidade, entidade_id)
    elif operacao == "edicao":
        return processar_edicao_dados(tipo_entidade, entidade, entidade_id)
    else:
        return {
            "resposta": "Operação não suportada.",
            "dados": {},
            "consulta": "",
            "estado_conversacional": None,
        }


def processar_exclusao_dados(
    tipo_entidade: str, entidade: dict, entidade_id: int
) -> dict:
    """
    Processa exclusão de dados com confirmação de segurança.
    """
    try:
        if tipo_entidade == "cliente":
            nome = entidade.get("nome", "Cliente")
            resposta = f"""⚠️ Você está prestes a excluir o cliente "{nome}".

Esta ação é irreversível e também excluirá todas as ordens de serviço relacionadas a este cliente.

Tem certeza que deseja continuar? Responda 'sim' para confirmar ou 'cancelar' para desistir."""

        elif tipo_entidade == "os":
            numero = entidade.get("numeroOS", "OS")
            cliente = entidade.get("clienteNome", "Cliente")
            resposta = f"""⚠️ Você está prestes a excluir a {numero} do cliente "{cliente}".

Esta ação é irreversível. Tem certeza que deseja continuar? Responda 'sim' para confirmar ou 'cancelar' para desistir."""

        elif tipo_entidade == "produto":
            nome = entidade.get("nome", "Produto")
            codigo = entidade.get("codigo", "Código")
            resposta = f"""⚠️ Você está prestes a excluir o produto "{nome}" (Código: {codigo}).

Esta ação é irreversível. Tem certeza que deseja continuar? Responda 'sim' para confirmar ou 'cancelar' para desistir."""

        else:
            return {
                "resposta": "Tipo de entidade não suportado para exclusão.",
                "dados": {},
                "consulta": "",
                "estado_conversacional": None,
            }

        # Iniciar fluxo de confirmação
        estado = {
            "modo": f"exclusao_{tipo_entidade}",
            "etapa": 1,
            "dados": {
                "entidade_id": entidade_id,
                "tipo_entidade": tipo_entidade,
                "entidade": entidade,
            },
        }

        return {
            "resposta": resposta,
            "dados": {"tipo": "confirmacao_exclusao"},
            "consulta": "",
            "estado_conversacional": estado,
        }

    except Exception as e:
        return {
            "resposta": f"Erro ao processar exclusão: {str(e)}",
            "dados": {},
            "consulta": "",
            "estado_conversacional": None,
        }


def processar_edicao_dados(
    tipo_entidade: str, entidade: dict, entidade_id: int
) -> dict:
    """
    Processa edição de dados - por enquanto apenas inicia o fluxo.
    """
    try:
        if tipo_entidade == "cliente":
            nome = entidade.get("nome", "Cliente")
            resposta = f"""Para editar o cliente "{nome}", você pode alterar:

• Nome
• Telefone  
• Email
• Endereço
• Observações

O que você gostaria de alterar? Por exemplo: "alterar telefone para 11999999999" """

        elif tipo_entidade == "os":
            numero = entidade.get("numeroOS", "OS")
            resposta = f"""Para editar a {numero}, você pode alterar:

• Status (aguardando, em_reparo, pronto, entregue)
• Valor do orçamento
• Diagnóstico técnico
• Observações

O que você gostaria de alterar? Por exemplo: "alterar status para pronto" """

        elif tipo_entidade == "produto":
            nome = entidade.get("nome", "Produto")
            resposta = f"""Para editar o produto "{nome}", você pode alterar:

• Nome
• Categoria
• Quantidade em estoque
• Preços (custo e venda)
• Descrição

O que você gostaria de alterar? Por exemplo: "alterar quantidade para 50" """

        else:
            return {
                "resposta": "Tipo de entidade não suportado para edição.",
                "dados": {},
                "consulta": "",
                "estado_conversacional": None,
            }

        # Iniciar fluxo de edição
        estado = {
            "modo": f"edicao_{tipo_entidade}",
            "etapa": 1,
            "dados": {
                "entidade_id": entidade_id,
                "tipo_entidade": tipo_entidade,
                "entidade": entidade,
            },
        }

        return {
            "resposta": resposta,
            "dados": {"tipo": "fluxo_edicao", "modo": estado["modo"]},
            "consulta": "",
            "estado_conversacional": estado,
        }

    except Exception as e:
        return {
            "resposta": f"Erro ao processar edição: {str(e)}",
            "dados": {},
            "consulta": "",
            "estado_conversacional": None,
        }


def processar_confirmacao_exclusao(
    consulta: str, estado: dict, dados_contexto: dict
) -> dict:
    """
    Processa a confirmação de exclusão de dados.
    """
    consulta_lower = consulta.lower().strip()
    dados = estado.get("dados", {})
    tipo_entidade = dados.get("tipo_entidade")
    entidade_id = dados.get("entidade_id")
    entidade = dados.get("entidade", {})

    # Verificar cancelamento
    if consulta_lower in ["cancelar", "cancela", "nao", "não", "parar", "sair"]:
        nome = entidade.get(
            "nome", entidade.get("numeroOS", entidade.get("codigo", "Item"))
        )
        return {
            "resposta": f"Ok, mantive o {tipo_entidade} '{nome}' sem alterações.",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": None,
        }

    # Verificar confirmação
    if any(
        confirmacao in consulta_lower
        for confirmacao in [
            "sim",
            "confirmar",
            "confirme",
            "pode excluir",
            "excluir mesmo",
            "ok",
            "certo",
        ]
    ):
        try:
            # Executar exclusão baseada no tipo de entidade
            if tipo_entidade == "cliente":
                # Excluir cliente
                from routes_clientes import Cliente

                cliente = Cliente.query.get(entidade_id)
                if cliente:
                    Cliente.query.filter_by(id=entidade_id).delete()
                    return {
                        "resposta": f"✅ Cliente '{entidade.get('nome', 'Cliente')}' excluído com sucesso!",
                        "dados": {"tipo": "cliente_excluido", "id": entidade_id},
                        "consulta": consulta,
                        "estado_conversacional": None,
                        "acao": {"tipo": "excluir_cliente", "id": entidade_id},
                    }

            elif tipo_entidade == "os":
                # Excluir OS
                from routes_os import OrdemServico

                os_obj = OrdemServico.query.get(entidade_id)
                if os_obj:
                    OrdemServico.query.filter_by(id=entidade_id).delete()
                    return {
                        "resposta": f"✅ OS '{entidade.get('numeroOS', 'OS')}' excluída com sucesso!",
                        "dados": {"tipo": "os_excluida", "id": entidade_id},
                        "consulta": consulta,
                        "estado_conversacional": None,
                        "acao": {"tipo": "excluir_os", "id": entidade_id},
                    }

            elif tipo_entidade == "produto":
                # Excluir produto
                from routes_estoque import ProdutoEstoque

                produto = ProdutoEstoque.query.get(entidade_id)
                if produto:
                    ProdutoEstoque.query.filter_by(id=entidade_id).delete()
                    return {
                        "resposta": f"✅ Produto '{entidade.get('nome', 'Produto')}' excluído com sucesso!",
                        "dados": {"tipo": "produto_excluido", "id": entidade_id},
                        "consulta": consulta,
                        "estado_conversacional": None,
                        "acao": {"tipo": "excluir_produto", "id": entidade_id},
                    }

            # Commit das alterações
            from extensions import db

            db.session.commit()

        except Exception as e:
            return {
                "resposta": f"❌ Erro ao excluir {tipo_entidade}: {str(e)}",
                "dados": {},
                "consulta": consulta,
                "estado_conversacional": None,
            }

    # Comando não reconhecido
    return {
        "resposta": "Por favor, responda 'sim' para confirmar a exclusão ou 'cancelar' para desistir.",
        "dados": {},
        "consulta": consulta,
        "estado_conversacional": estado,
    }


def processar_fluxo_edicao(consulta: str, estado: dict, dados_contexto: dict) -> dict:
    """
    Processa o fluxo de edição de dados.
    """
    consulta_lower = consulta.lower().strip()
    dados = estado.get("dados", {})
    tipo_entidade = dados.get("tipo_entidade")
    entidade_id = dados.get("entidade_id")
    entidade = dados.get("entidade", {})

    # Verificar cancelamento
    if consulta_lower in ["cancelar", "cancela", "parar", "sair"]:
        nome = entidade.get(
            "nome", entidade.get("numeroOS", entidade.get("codigo", "Item"))
        )
        return {
            "resposta": f"Ok, mantive o {tipo_entidade} '{nome}' sem alterações.",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": None,
        }

    # Para simplificar, vamos detectar alterações específicas por palavra-chave
    try:
        if tipo_entidade == "cliente":
            # Detectar alterações para cliente
            if "telefone" in consulta_lower or "fone" in consulta_lower:
                # Extrair novo telefone
                import re

                telefone_match = re.search(
                    r"(\d{2}[\s\-\.]?\d{4,5}[\s\-\.]?\d{4})", consulta
                )
                if telefone_match:
                    novo_telefone = (
                        telefone_match.group(1)
                        .replace(" ", "")
                        .replace("-", "")
                        .replace(".", "")
                    )
                    if len(novo_telefone) >= 10:
                        # Atualizar cliente
                        from routes_clientes import Cliente

                        cliente = Cliente.query.get(entidade_id)
                        if cliente:
                            cliente.telefone = novo_telefone
                            from extensions import db

                            db.session.commit()
                            return {
                                "resposta": f"✅ Telefone do cliente '{cliente.nome}' atualizado para {novo_telefone}!",
                                "dados": {
                                    "tipo": "cliente_atualizado",
                                    "id": entidade_id,
                                },
                                "consulta": consulta,
                                "estado_conversacional": None,
                                "acao": {
                                    "tipo": "atualizar_cliente",
                                    "id": entidade_id,
                                    "campo": "telefone",
                                    "valor": novo_telefone,
                                },
                            }

            elif "email" in consulta_lower:
                # Extrair novo email
                import re

                email_match = re.search(
                    r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", consulta
                )
                if email_match:
                    novo_email = email_match.group(1)
                    # Atualizar cliente
                    from routes_clientes import Cliente

                    cliente = Cliente.query.get(entidade_id)
                    if cliente:
                        cliente.email = novo_email
                        from extensions import db

                        db.session.commit()
                        return {
                            "resposta": f"✅ Email do cliente '{cliente.nome}' atualizado para {novo_email}!",
                            "dados": {"tipo": "cliente_atualizado", "id": entidade_id},
                            "consulta": consulta,
                            "estado_conversacional": None,
                            "acao": {
                                "tipo": "atualizar_cliente",
                                "id": entidade_id,
                                "campo": "email",
                                "valor": novo_email,
                            },
                        }

        elif tipo_entidade == "os":
            # Detectar alterações para OS
            if "status" in consulta_lower:
                status_map = {
                    "aguardando": "aguardando",
                    "em reparo": "em_reparo",
                    "reparo": "em_reparo",
                    "pronto": "pronto",
                    "entregue": "entregue",
                }
                novo_status = None
                for chave, valor in status_map.items():
                    if chave in consulta_lower:
                        novo_status = valor
                        break

                if novo_status:
                    from routes_os import OrdemServico

                    os_obj = OrdemServico.query.get(entidade_id)
                    if os_obj:
                        os_obj.status = novo_status
                        from extensions import db

                        db.session.commit()
                        return {
                            "resposta": f"✅ Status da OS '{os_obj.numero_os}' atualizado para '{novo_status}'!",
                            "dados": {"tipo": "os_atualizada", "id": entidade_id},
                            "consulta": consulta,
                            "estado_conversacional": None,
                            "acao": {
                                "tipo": "atualizar_os",
                                "id": entidade_id,
                                "campo": "status",
                                "valor": novo_status,
                            },
                        }

        elif tipo_entidade == "produto":
            # Detectar alterações para produto
            if "quantidade" in consulta_lower:
                import re

                qtd_match = re.search(r"(\d+)", consulta)
                if qtd_match:
                    nova_qtd = int(qtd_match.group(1))
                    from routes_estoque import ProdutoEstoque

                    produto = ProdutoEstoque.query.get(entidade_id)
                    if produto:
                        produto.quantidade = nova_qtd
                        from extensions import db

                        db.session.commit()
                        return {
                            "resposta": f"✅ Quantidade do produto '{produto.nome}' atualizada para {nova_qtd}!",
                            "dados": {"tipo": "produto_atualizado", "id": entidade_id},
                            "consulta": consulta,
                            "estado_conversacional": None,
                            "acao": {
                                "tipo": "atualizar_produto",
                                "id": entidade_id,
                                "campo": "quantidade",
                                "valor": nova_qtd,
                            },
                        }

        # Se não conseguiu identificar a alteração
        return {
            "resposta": f"Não consegui identificar a alteração desejada. Por favor, seja mais específico. Por exemplo: 'alterar telefone para 11999999999'",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": estado,
        }

    except Exception as e:
        return {
            "resposta": f"Erro ao processar edição: {str(e)}",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": None,
        }


def detectar_pergunta_conversacional(consulta_lower: str) -> str:
    """
    Detecta perguntas conversacionais e retorna respostas apropriadas.
    Retorna None se não for uma pergunta conversacional.
    """
    # Saudações
    if any(
        saudacao in consulta_lower
        for saudacao in [
            "oi",
            "olá",
            "ola",
            "bom dia",
            "boa tarde",
            "boa noite",
            "e ai",
            "eae",
        ]
    ):
        return "Olá! Como posso ajudar você hoje com seus clientes, ordens de serviço ou produtos?"

    # Sobre a própria IA
    if any(
        pergunta in consulta_lower
        for pergunta in [
            "voce é uma ia",
            "você é uma ia",
            "é uma ia",
            "voce é um robo",
            "você é um robo",
            "o que voce é",
            "o que você é",
            "quem é voce",
            "quem é você",
        ]
    ):
        return "Sim, sou uma IA assistente especializada em gestão de assistência técnica! Posso ajudar você a consultar dados, criar clientes, ordens de serviço e gerenciar seu negócio."

    # Capacidades da IA
    if any(
        pergunta in consulta_lower
        for pergunta in [
            "o que voce faz",
            "o que você faz",
            "o que pode fazer",
            "suas funcoes",
            "suas funções",
            "como voce ajuda",
            "como você ajuda",
            "para que serve",
        ]
    ):
        return "Posso ajudar você com: consultar dados de clientes e OS, criar novos registros via conversa, gerar relatórios financeiros, gerenciar estoque e muito mais! O que você gostaria de saber?"

    # Agradecimentos
    if any(
        agradecimento in consulta_lower
        for agradecimento in [
            "obrigado",
            "obrigada",
            "valeu",
            "thanks",
            "thank you",
            "agradecido",
        ]
    ):
        return "De nada! Estou sempre aqui para ajudar com sua gestão de assistência técnica."

    # Confirmações positivas
    if any(
        confirmacao in consulta_lower
        for confirmacao in [
            "entendi",
            "entendi",
            "beleza",
            "ok",
            "okay",
            "certo",
            "claro",
            "perfeito",
            "ótimo",
            "otimo",
            "bom",
            "show",
            "legal",
        ]
    ):
        return "Que bom! Posso ajudar com mais alguma coisa sobre seus clientes, OS ou produtos?"

    # Despedidas
    if any(
        despedida in consulta_lower
        for despedida in [
            "tchau",
            "até logo",
            "ate logo",
            "até mais",
            "ate mais",
            "bye",
            "falou",
        ]
    ):
        return "Até logo! Quando precisar de ajuda com sua assistência técnica, estarei aqui."

    # Perguntas sobre o sistema
    if any(
        pergunta in consulta_lower
        for pergunta in [
            "como funciona",
            "como funciona o sistema",
            "como usar",
            "ajuda",
            "help",
        ]
    ):
        return "Posso ajudar você a: consultar clientes (digite o nome), ver status de OS (digite o número), criar novos registros, ver relatórios financeiros, etc. O que você gostaria de fazer?"

    # Não é uma pergunta conversacional
    return None


def melhorar_busca_com_fuzzy(
    consulta: str, entidades: list, campo_nome: str, campo_codigo: str = None
) -> dict:
    """
    Melhora a busca usando fuzzy matching se disponível.
    Retorna a melhor correspondência encontrada.
    """
    try:
        from fuzzywuzzy import fuzz
        from fuzzywuzzy import process
    except ImportError:
        # Fallback para busca simples se fuzzywuzzy não estiver disponível
        return None

    if not entidades:
        return None

    # Preparar lista de nomes para busca
    nomes = [entidade[campo_nome] for entidade in entidades]

    # Buscar melhor correspondência usando fuzzywuzzy
    melhor_match, score = process.extractOne(
        consulta, nomes, scorer=fuzz.token_sort_ratio
    )

    # Só aceitar se score for alto o suficiente (>70%)
    if score > 70:
        # Encontrar a entidade correspondente
        for entidade in entidades:
            if entidade[campo_nome] == melhor_match:
                return {"entidade": entidade, "score": score, "tipo": "fuzzy_match"}

    # Tentar também com códigos se disponível
    if campo_codigo:
        codigos = []
        for entidade in entidades:
            if entidade.get(campo_codigo):
                codigos.append(entidade[campo_codigo])

        if codigos:
            melhor_codigo_match, codigo_score = process.extractOne(
                consulta, codigos, scorer=fuzz.ratio
            )
            if codigo_score > 80:  # Score mais alto para códigos
                for entidade in entidades:
                    if entidade.get(campo_codigo) == melhor_codigo_match:
                        return {
                            "entidade": entidade,
                            "score": codigo_score,
                            "tipo": "codigo_fuzzy_match",
                        }

    return None
