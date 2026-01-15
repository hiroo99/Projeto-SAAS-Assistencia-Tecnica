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


def interpretar_consulta_ia(consulta: str, dados_contexto: dict, estado_conversacional: dict = None) -> dict:
    """
    Interpreta uma consulta em linguagem natural e extrai informações dos dados disponíveis.
    Suporta criação conversacional de dados (clientes, OS, produtos).
    Retorna uma resposta estruturada com a informação solicitada.
    """
    try:
        consulta_lower = consulta.lower()

        # Verificar se estamos em um fluxo conversacional de criação
        if estado_conversacional and estado_conversacional.get('modo'):
            return processar_fluxo_conversacional(consulta, estado_conversacional, dados_contexto)

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
            "estado_conversacional": None  # Não há fluxo conversacional ativo
        }

    except Exception as e:
        print(f"Erro ao interpretar consulta IA: {e}")
        return {
            "resposta": "Desculpe, não foi possível processar sua consulta no momento.",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": None
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


def detectar_intencao_criacao(consulta_lower: str) -> str:
    """
    Detecta se o usuário quer criar dados (cliente, OS, produto).
    Retorna o tipo de criação ou None.
    """
    # Padrões para detectar intenção de criação
    padroes_cliente = [
        'adicionar cliente', 'cadastrar cliente', 'criar cliente', 'novo cliente',
        'registrar cliente', 'incluir cliente', 'quero adicionar um cliente',
        'gostaria de adicionar um cliente'
    ]

    padroes_os = [
        'criar os', 'nova os', 'adicionar os', 'cadastrar os', 'registrar os',
        'nova ordem', 'ordem de serviço', 'quero criar uma os'
    ]

    padroes_produto = [
        'adicionar produto', 'cadastrar produto', 'criar produto', 'novo produto',
        'registrar produto', 'incluir produto', 'quero adicionar um produto'
    ]

    for padrao in padroes_cliente:
        if padrao in consulta_lower:
            return 'cliente'

    for padrao in padroes_os:
        if padrao in consulta_lower:
            return 'os'

    for padrao in padroes_produto:
        if padrao in consulta_lower:
            return 'produto'

    return None


def iniciar_fluxo_criacao(tipo: str, dados_contexto: dict) -> dict:
    """
    Inicia um fluxo conversacional para criação de dados.
    """
    if tipo == 'cliente':
        estado = {
            "modo": "criacao_cliente",
            "etapa": 1,
            "dados": {},
            "campos_obrigatorios": ["nome", "cpfCnpj", "telefone"],
            "campos_opcionais": ["email", "endereco", "observacoes"],
            "proximo_campo": "nome"
        }
        resposta = "Certo! Vou ajudar você a cadastrar um novo cliente. Qual o nome completo do cliente?"

    elif tipo == 'os':
        estado = {
            "modo": "criacao_os",
            "etapa": 1,
            "dados": {},
            "campos_obrigatorios": ["clienteId", "tipoAparelho", "marcaModelo", "problemaRelatado"],
            "campos_opcionais": ["imeiSerial", "corAparelho", "valorOrcamento", "observacoes"],
            "proximo_campo": "cliente"
        }
        resposta = "Perfeito! Vou criar uma nova Ordem de Serviço. Primeiro, preciso saber qual cliente. Você pode informar o nome do cliente ou seu ID."

    elif tipo == 'produto':
        estado = {
            "modo": "criacao_produto",
            "etapa": 1,
            "dados": {},
            "campos_obrigatorios": ["nome", "categoria", "codigo"],
            "campos_opcionais": ["descricao", "quantidade", "estoqueMinimo", "precoCusto", "precoVenda", "fornecedor", "localizacao"],
            "proximo_campo": "nome"
        }
        resposta = "Excelente! Vou cadastrar um novo produto. Qual o nome do produto?"

    else:
        return {
            "resposta": "Desculpe, não entendi o tipo de dado que você quer criar.",
            "dados": {},
            "consulta": "",
            "estado_conversacional": None
        }

    return {
        "resposta": resposta,
        "dados": {"tipo": "fluxo_criacao", "modo": estado["modo"]},
        "consulta": "",
        "estado_conversacional": estado
    }


def processar_fluxo_conversacional(consulta: str, estado: dict, dados_contexto: dict) -> dict:
    """
    Processa uma resposta dentro de um fluxo conversacional de criação.
    """
    modo = estado.get('modo')

    if modo == 'criacao_cliente':
        return processar_criacao_cliente(consulta, estado, dados_contexto)
    elif modo == 'criacao_os':
        return processar_criacao_os(consulta, estado, dados_contexto)
    elif modo == 'criacao_produto':
        return processar_criacao_produto(consulta, estado, dados_contexto)
    else:
        # Finalizar fluxo se modo desconhecido
        return {
            "resposta": "Ocorreu um erro no fluxo conversacional. Vamos recomeçar.",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": None
        }


def processar_criacao_cliente(consulta: str, estado: dict, dados_contexto: dict) -> dict:
    """
    Processa o fluxo de criação de cliente.
    """
    etapa = estado.get('etapa', 1)
    dados = estado.get('dados', {})
    campos_obrigatorios = estado.get('campos_obrigatorios', [])
    campos_opcionais = estado.get('campos_opcionais', [])

    # Verificar comandos especiais
    consulta_lower = consulta.lower().strip()
    if consulta_lower in ['cancelar', 'cancela', 'parar', 'sair']:
        return {
            "resposta": "Ok, cancelei o cadastro do cliente.",
            "dados": {},
            "consulta": consulta,
            "estado_conversacional": None
        }

    # Processar conforme etapa
    if etapa == 1:  # Nome
        if not consulta.strip():
            resposta = "Por favor, informe o nome completo do cliente:"
        else:
            dados['nome'] = consulta.strip()
            estado['dados'] = dados
            estado['etapa'] = 2
            estado['proximo_campo'] = 'cpfCnpj'
            resposta = "Perfeito! Agora preciso do CPF ou CNPJ do cliente:"

    elif etapa == 2:  # CPF/CNPJ
        # Validação básica de CPF/CNPJ
        cpf_limpo = consulta.replace('.', '').replace('-', '').replace('/', '').strip()
        if len(cpf_limpo) < 11:
            resposta = "CPF/CNPJ parece estar incompleto. Por favor, digite novamente:"
        elif not cpf_limpo.isdigit():
            resposta = "CPF/CNPJ deve conter apenas números. Por favor, digite novamente:"
        else:
            # Verificar se já existe
            cpf_existe = any(c['cpf_cnpj'].replace('.', '').replace('-', '').replace('/', '') == cpf_limpo
                           for c in dados_contexto.get('clientes', []))
            if cpf_existe:
                resposta = "Este CPF/CNPJ já está cadastrado no sistema. Por favor, verifique ou use outro:"
            else:
                dados['cpfCnpj'] = consulta.strip()
                estado['dados'] = dados
                estado['etapa'] = 3
                estado['proximo_campo'] = 'telefone'
                resposta = "Ótimo! Agora qual o telefone de contato?"

    elif etapa == 3:  # Telefone
        telefone_limpo = consulta.replace('(', '').replace(')', '').replace('-', '').replace(' ', '').strip()
        if len(telefone_limpo) < 10:
            resposta = "Telefone parece estar incompleto. Por favor, digite novamente:"
        elif not telefone_limpo.isdigit():
            resposta = "Telefone deve conter apenas números. Por favor, digite novamente:"
        else:
            dados['telefone'] = consulta.strip()
            estado['dados'] = dados
            estado['etapa'] = 4
            estado['proximo_campo'] = 'confirmacao'

            # Resumo para confirmação
            resposta = f"Excelente! Aqui está o resumo do cliente:\n\n📝 Nome: {dados['nome']}\n🆔 CPF/CNPJ: {dados['cpfCnpj']}\n📞 Telefone: {dados['telefone']}\n\nDeseja confirmar o cadastro ou adicionar mais informações (email, endereço)?"

    elif etapa == 4:  # Confirmação/Finalização
        if any(palavra in consulta_lower for palavra in ['sim', 'confirmar', 'ok', 'certo', 'cadastrar']):
            # Tentar criar o cliente
            try:
                # Preparar dados de criação incluindo campos opcionais
                dados_criacao = {
                    "nome": dados['nome'],
                    "cpfCnpj": dados['cpfCnpj'],
                    "telefone": dados['telefone'],
                    "status": "ativo"
                }

                # Adicionar campos opcionais se foram fornecidos
                if 'email' in dados and dados['email']:
                    dados_criacao['email'] = dados['email']
                if 'endereco' in dados and dados['endereco']:
                    dados_criacao['endereco'] = dados['endereco']
                if 'observacoes' in dados and dados['observacoes']:
                    dados_criacao['observacoes'] = dados['observacoes']

                return {
                    "resposta": f"✅ Cliente '{dados['nome']}' cadastrado com sucesso!",
                    "dados": {
                        "tipo": "cliente_criado",
                        "dados": dados_criacao
                    },
                    "consulta": consulta,
                    "estado_conversacional": None,
                    "acao": {
                        "tipo": "criar_cliente",
                        "dados": dados_criacao
                    }
                }
            except Exception as e:
                return {
                    "resposta": f"❌ Ocorreu um erro ao cadastrar o cliente: {str(e)}",
                    "dados": {},
                    "consulta": consulta,
                    "estado_conversacional": estado  # Manter estado para tentar novamente
                }

        elif any(palavra in consulta_lower for palavra in ['email', 'endereco', 'mais']):
            estado['etapa'] = 5
            resposta = "Certo! Qual informação adicional você quer adicionar? (email, endereço ou observações)"

        else:
            resposta = "Por favor, diga 'sim' para confirmar ou 'email/endereço' para adicionar mais informações:"

    elif etapa == 5:  # Campos opcionais
        if 'email' in consulta_lower:
            estado['etapa'] = 6
            resposta = "Qual o endereço de email do cliente?"
        elif 'endereco' in consulta_lower or 'endereço' in consulta_lower:
            estado['etapa'] = 7
            resposta = "Qual o endereço completo do cliente?"
        elif 'observacoes' in consulta_lower or 'observações' in consulta_lower:
            estado['etapa'] = 8
            resposta = "Quais as observações sobre o cliente?"
        else:
            resposta = "Por favor, escolha: email, endereço ou observações:"

    elif etapa == 6:  # Email
        dados['email'] = consulta.strip()
        estado['dados'] = dados
        estado['etapa'] = 4  # Volta para confirmação
        resposta = f"Email adicionado! Aqui está o resumo atualizado:\n\n📝 Nome: {dados['nome']}\n🆔 CPF/CNPJ: {dados['cpfCnpj']}\n📞 Telefone: {dados['telefone']}\n📧 Email: {dados['email']}\n\nDeseja confirmar o cadastro ou adicionar mais informações?"

    elif etapa == 7:  # Endereço
        dados['endereco'] = consulta.strip()
        estado['dados'] = dados
        estado['etapa'] = 4  # Volta para confirmação
        resposta = f"Endereço adicionado! Aqui está o resumo atualizado:\n\n📝 Nome: {dados['nome']}\n🆔 CPF/CNPJ: {dados['cpfCnpj']}\n📞 Telefone: {dados['telefone']}\n🏠 Endereço: {dados['endereco']}\n\nDeseja confirmar o cadastro ou adicionar mais informações?"

    elif etapa == 8:  # Observações
        dados['observacoes'] = consulta.strip()
        estado['dados'] = dados
        estado['etapa'] = 4  # Volta para confirmação
        resposta = f"Observações adicionadas! Aqui está o resumo atualizado:\n\n📝 Nome: {dados['nome']}\n🆔 CPF/CNPJ: {dados['cpfCnpj']}\n📞 Telefone: {dados['telefone']}\n📝 Observações: {dados['observacoes']}\n\nDeseja confirmar o cadastro ou adicionar mais informações?"

    else:
        resposta = "Ocorreu um erro no fluxo. Vamos recomeçar."

    return {
        "resposta": resposta,
        "dados": {"tipo": "fluxo_continuacao"},
        "consulta": consulta,
        "estado_conversacional": estado
    }


def processar_criacao_os(consulta: str, estado: dict, dados_contexto: dict) -> dict:
    """
    Processa o fluxo de criação de OS (placeholder para implementação futura).
    """
    return {
        "resposta": "Funcionalidade de criação de OS ainda em desenvolvimento. Por enquanto, use o formulário normal.",
        "dados": {},
        "consulta": consulta,
        "estado_conversacional": None
    }


def processar_criacao_produto(consulta: str, estado: dict, dados_contexto: dict) -> dict:
    """
    Processa o fluxo de criação de produto (placeholder para implementação futura).
    """
    return {
        "resposta": "Funcionalidade de criação de produto ainda em desenvolvimento. Por enquanto, use o formulário normal.",
        "dados": {},
        "consulta": consulta,
        "estado_conversacional": None
    }
