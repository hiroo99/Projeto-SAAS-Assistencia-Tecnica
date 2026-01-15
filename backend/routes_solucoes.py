from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import SolucoesDocument, OrdemServico, Cliente

bp = Blueprint("solucoes", __name__, url_prefix="/api/solucoes")


@bp.route("/", methods=["GET"])
def listar_solucoes():
    """Lista todas as soluções documentadas."""
    try:
        solucoes = SolucoesDocument.query.all()
        return jsonify(
            [
                {
                    "id": s.id,
                    "os_id": s.os_id,
                    "numero": s.numero,
                    "data": s.data.isoformat() if s.data else None,
                    "idcliente": s.idcliente,
                    "nome_cliente": s.cliente.nome if s.cliente else None,
                    "descricao_problema": s.descricao_problema,
                    "marca": s.marca,
                    "tipo": s.tipo,
                    "data_abertura": (
                        s.data_abertura.isoformat() if s.data_abertura else None
                    ),
                    "data_fechamento": (
                        s.data_fechamento.isoformat() if s.data_fechamento else None
                    ),
                    "diagnostico_ia": s.diagnostico_ia,
                    "solucoes_ia": s.solucoes_ia,
                    "criado_em": s.criado_em.isoformat() if s.criado_em else None,
                    "atualizado_em": (
                        s.atualizado_em.isoformat() if s.atualizado_em else None
                    ),
                }
                for s in solucoes
            ]
        )
    except Exception as e:
        print(f"Erro ao listar soluções: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@bp.route("/<int:id>", methods=["GET"])
def obter_solucao(id):
    """Obtém uma solução específica por ID."""
    try:
        solucao = SolucoesDocument.query.get_or_404(id)
        return jsonify(
            {
                "id": solucao.id,
                "os_id": solucao.os_id,
                "numero": solucao.numero,
                "data": solucao.data.isoformat() if solucao.data else None,
                "idcliente": solucao.idcliente,
                "nome_cliente": solucao.cliente.nome if solucao.cliente else None,
                "descricao_problema": solucao.descricao_problema,
                "marca": solucao.marca,
                "tipo": solucao.tipo,
                "data_abertura": (
                    solucao.data_abertura.isoformat() if solucao.data_abertura else None
                ),
                "data_fechamento": (
                    solucao.data_fechamento.isoformat()
                    if solucao.data_fechamento
                    else None
                ),
                "diagnostico_ia": solucao.diagnostico_ia,
                "solucoes_ia": solucao.solucoes_ia,
                "criado_em": (
                    solucao.criado_em.isoformat() if solucao.criado_em else None
                ),
                "atualizado_em": (
                    solucao.atualizado_em.isoformat() if solucao.atualizado_em else None
                ),
            }
        )
    except Exception as e:
        print(f"Erro ao obter solução {id}: {e}")
        return jsonify({"erro": "Solução não encontrada"}), 404


@bp.route("/", methods=["POST"])
def criar_solucao():
    """Cria uma nova solução documentada."""
    try:
        dados = request.get_json()

        # Validar dados obrigatórios
        campos_obrigatorios = [
            "os_id",
            "numero",
            "data",
            "idcliente",
            "descricao_problema",
            "marca",
            "tipo",
            "data_abertura",
        ]

        for campo in campos_obrigatorios:
            if campo not in dados or dados[campo] is None:
                return jsonify({"erro": f"Campo obrigatório: {campo}"}), 400

        # Verificar se a OS existe
        os = OrdemServico.query.get(dados["os_id"])
        if not os:
            return jsonify({"erro": "Ordem de serviço não encontrada"}), 404

        # Verificar se o cliente existe
        cliente = Cliente.query.get(dados["idcliente"])
        if not cliente:
            return jsonify({"erro": "Cliente não encontrado"}), 404

        # Criar nova solução
        nova_solucao = SolucoesDocument(
            os_id=dados["os_id"],
            numero=dados["numero"],
            data=dados["data"],
            idcliente=dados["idcliente"],
            descricao_problema=dados["descricao_problema"],
            marca=dados["marca"],
            tipo=dados["tipo"],
            data_abertura=dados["data_abertura"],
            data_fechamento=dados.get("data_fechamento"),
            diagnostico_ia=dados.get("diagnostico_ia"),
            solucoes_ia=dados.get("solucoes_ia"),
        )

        db.session.add(nova_solucao)
        db.session.commit()

        return (
            jsonify({"id": nova_solucao.id, "mensagem": "Solução criada com sucesso"}),
            201,
        )

    except IntegrityError as e:
        db.session.rollback()
        error_str = str(e.orig).lower() if hasattr(e, "orig") else str(e).lower()
        if "unique constraint failed" in error_str:
            return jsonify({"erro": "Já existe uma solução para esta OS"}), 409
        return jsonify({"erro": "Erro de integridade no banco de dados"}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar solução: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@bp.route("/<int:id>", methods=["PUT"])
def atualizar_solucao(id):
    """Atualiza uma solução existente."""
    try:
        solucao = SolucoesDocument.query.get_or_404(id)
        dados = request.get_json()

        # Verificar se a OS existe (se fornecido)
        if "os_id" in dados:
            os = OrdemServico.query.get(dados["os_id"])
            if not os:
                return jsonify({"erro": "Ordem de serviço não encontrada"}), 404
            solucao.os_id = dados["os_id"]

        # Verificar se o cliente existe (se fornecido)
        if "idcliente" in dados:
            cliente = Cliente.query.get(dados["idcliente"])
            if not cliente:
                return jsonify({"erro": "Cliente não encontrado"}), 404
            solucao.idcliente = dados["idcliente"]

        # Atualizar campos permitidos
        campos_atualizaveis = [
            "numero",
            "data",
            "descricao_problema",
            "marca",
            "tipo",
            "data_abertura",
            "data_fechamento",
            "diagnostico_ia",
            "solucoes_ia",
        ]

        for campo in campos_atualizaveis:
            if campo in dados:
                setattr(solucao, campo, dados[campo])

        db.session.commit()

        return jsonify({"mensagem": "Solução atualizada com sucesso"})

    except IntegrityError as e:
        db.session.rollback()
        error_str = str(e.orig).lower() if hasattr(e, "orig") else str(e).lower()
        if "unique constraint failed" in error_str:
            return jsonify({"erro": "Já existe uma solução para esta OS"}), 409
        return jsonify({"erro": "Erro de integridade no banco de dados"}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar solução {id}: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@bp.route("/<int:id>", methods=["DELETE"])
def deletar_solucao(id):
    """Remove uma solução."""
    try:
        solucao = SolucoesDocument.query.get_or_404(id)

        db.session.delete(solucao)
        db.session.commit()

        return jsonify({"mensagem": "Solução removida com sucesso"})

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar solução {id}: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500


@bp.route("/os/<int:os_id>", methods=["GET"])
def obter_solucao_por_os(os_id):
    """Obtém soluções para uma OS específica."""
    try:
        # Verificar se a OS existe
        os = OrdemServico.query.get(os_id)
        if not os:
            return jsonify({"erro": "Ordem de serviço não encontrada"}), 404

        solucoes = SolucoesDocument.query.filter_by(os_id=os_id).all()

        return jsonify(
            [
                {
                    "id": s.id,
                    "os_id": s.os_id,
                    "numero": s.numero,
                    "data": s.data.isoformat() if s.data else None,
                    "idcliente": s.idcliente,
                    "nome_cliente": s.cliente.nome if s.cliente else None,
                    "descricao_problema": s.descricao_problema,
                    "marca": s.marca,
                    "tipo": s.tipo,
                    "data_abertura": (
                        s.data_abertura.isoformat() if s.data_abertura else None
                    ),
                    "data_fechamento": (
                        s.data_fechamento.isoformat() if s.data_fechamento else None
                    ),
                    "diagnostico_ia": s.diagnostico_ia,
                    "solucoes_ia": s.solucoes_ia,
                    "criado_em": s.criado_em.isoformat() if s.criado_em else None,
                    "atualizado_em": (
                        s.atualizado_em.isoformat() if s.atualizado_em else None
                    ),
                }
                for s in solucoes
            ]
        )

    except Exception as e:
        print(f"Erro ao obter soluções para OS {os_id}: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
