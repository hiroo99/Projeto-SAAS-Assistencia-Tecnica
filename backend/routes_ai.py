from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from ai_utils import gerar_pre_diagnostico, gerar_resumo, interpretar_consulta_ia
from auth_utils import login_required
from models import Cliente, OrdemServico, ProdutoEstoque, Usuario, Notificacao
from extensions import db

bp = Blueprint("ai", __name__)


@bp.post("/resumo")
@login_required
def gerar_resumo_api():
    """Gera um resumo do problema relatado usando IA."""
    data = request.get_json() or {}

    problema = data.get("problema", "").strip()
    if not problema:
        return (
            jsonify(
                {
                    "erro": "Campo obrigatório",
                    "mensagem": "O campo 'problema' é obrigatório",
                }
            ),
            400,
        )

    try:
        resumo = gerar_resumo(problema)
        return jsonify({"resumo": resumo, "problema_original": problema})
    except Exception as e:
        print(f"Erro na geração de resumo: {e}")
        return (
            jsonify(
                {
                    "erro": "Erro na geração de resumo",
                    "mensagem": "Não foi possível gerar o resumo. Tente novamente.",
                }
            ),
            500,
        )


@bp.post("/diagnostico")
@login_required
def gerar_diagnostico_api():
    """Gera um pré-diagnóstico usando IA."""
    data = request.get_json() or {}

    tipo_aparelho = data.get("tipoAparelho", "").strip()
    marca_modelo = data.get("marcaModelo", "").strip()
    problema = data.get("problema", "").strip()

    if not all([tipo_aparelho, marca_modelo, problema]):
        return (
            jsonify(
                {
                    "erro": "Campos obrigatórios",
                    "mensagem": "Os campos 'tipoAparelho', 'marcaModelo' e 'problema' são obrigatórios",
                }
            ),
            400,
        )

    try:
        diagnostico = gerar_pre_diagnostico(tipo_aparelho, marca_modelo, problema)
        return jsonify(
            {
                "diagnostico": diagnostico,
                "tipoAparelho": tipo_aparelho,
                "marcaModelo": marca_modelo,
                "problema": problema,
            }
        )
    except Exception as e:
        print(f"Erro na geração de diagnóstico: {e}")
        return (
            jsonify(
                {
                    "erro": "Erro na geração de diagnóstico",
                    "mensagem": "Não foi possível gerar o pré-diagnóstico. Tente novamente.",
                }
            ),
            500,
        )


@bp.post("/consulta")
@login_required
def consulta_ia_api():
    """Processa consultas em linguagem natural usando IA."""
    data = request.get_json() or {}

    consulta = data.get("consulta", "").strip()
    estado_conversacional = data.get("estado_conversacional")  # Estado para fluxos conversacionais

    if not consulta:
        return (
            jsonify(
                {
                    "erro": "Campo obrigatório",
                    "mensagem": "O campo 'consulta' é obrigatório",
                }
            ),
            400,
        )

    try:
        # Coletar dados de contexto do sistema
        dados_contexto = coletar_dados_contexto()

        # Interpretar consulta usando IA (com suporte a estado conversacional)
        resultado = interpretar_consulta_ia(consulta, dados_contexto, estado_conversacional)

        # Se há uma ação para executar (como criar cliente), executa
        if resultado.get('acao'):
            acao = resultado['acao']
            if acao['tipo'] == 'criar_cliente':
                # Criar cliente via API
                try:
                    from routes_clientes import criar_cliente_interno

                    # Simular request para criar cliente
                    cliente_criado = criar_cliente_interno(acao['dados'])
                    resultado['dados']['cliente_criado'] = cliente_criado

                except Exception as e:
                    print(f"Erro ao criar cliente via IA: {e}")
                    resultado['resposta'] = "Cliente não pôde ser cadastrado devido a um erro técnico."
                    resultado['dados'] = {}

        return jsonify(resultado)

    except Exception as e:
        print(f"Erro na consulta IA: {e}")
        return (
            jsonify(
                {
                    "erro": "Erro na consulta IA",
                    "mensagem": "Não foi possível processar sua consulta. Tente novamente.",
                    "resposta": "Desculpe, houve um erro ao processar sua consulta.",
                    "consulta": consulta,
                    "estado_conversacional": estado_conversacional
                }
            ),
            500,
        )


def coletar_dados_contexto() -> dict:
    """
    Coleta dados de contexto de todas as tabelas para fornecer à IA.
    """
    try:
        # Buscar clientes
        clientes = Cliente.query.filter_by(status="ativo").limit(50).all()
        clientes_data = []
        for c in clientes:
            clientes_data.append({
                "id": c.id,
                "nome": c.nome,
                "cpf_cnpj": c.cpf_cnpj,
                "email": c.email,
                "telefone": c.telefone,
                "endereco": c.endereco
            })

        # Buscar OS com clientes
        os_data = []
        ordens = OrdemServico.query.options(joinedload(OrdemServico.cliente)).limit(100).all()
        for os in ordens:
            os_dict = {
                "id": os.id,
                "numeroOS": os.numero_os,
                "clienteId": os.cliente_id,
                "clienteNome": os.cliente.nome if os.cliente else "Cliente não informado",
                "tipoAparelho": os.tipo_aparelho,
                "marcaModelo": os.marca_modelo,
                "problemaRelatado": os.problema_relatado,
                "status": os.status,
                "valorOrcamento": float(os.valor_orcamento or 0),
                "dataCriacao": os.criado_em.isoformat() if os.criado_em else None
            }
            os_data.append(os_dict)

        # Buscar produtos
        produtos = ProdutoEstoque.query.limit(100).all()
        produtos_data = []
        for p in produtos:
            produtos_data.append({
                "id": p.id,
                "codigo": p.codigo,
                "nome": p.nome,
                "categoria": p.categoria,
                "quantidade": p.quantidade,
                "estoqueMinimo": p.estoque_minimo,
                "precoCusto": float(p.preco_custo or 0),
                "precoVenda": float(p.preco_venda or 0)
            })

        # Calcular métricas financeiras
        os_entregues = [os for os in ordens if os.status == 'entregue']
        receitas_totais = sum(float(os.valor_orcamento or 0) for os in os_entregues)

        return {
            "clientes": clientes_data,
            "total_clientes": len(clientes_data),
            "os": os_data,
            "total_os": len(os_data),
            "produtos": produtos_data,
            "total_produtos": len(produtos_data),
            "receitas_totais": receitas_totais,
            "os_entregues": len(os_entregues)
        }

    except Exception as e:
        print(f"Erro ao coletar dados de contexto: {e}")
        return {}
