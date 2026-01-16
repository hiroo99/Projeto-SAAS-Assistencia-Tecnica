from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Cliente, Usuario
from auth_utils import login_required, get_usuario_atual
from routes_notificacoes import criar_notificacao_cliente_novo

bp = Blueprint("clientes", __name__)


def cliente_to_dict(cliente: Cliente) -> dict:
    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "cpfCnpj": cliente.cpf_cnpj,
        "tipoPessoa": cliente.tipo_pessoa,
        "telefone": cliente.telefone,
        "email": cliente.email,
        "endereco": cliente.endereco,
        "observacoes": cliente.observacoes,
        "status": cliente.status,
        "dataCadastro": cliente.criado_em.isoformat() if cliente.criado_em else None,
        "dataAtualizacao": (
            cliente.atualizado_em.isoformat() if cliente.atualizado_em else None
        ),
    }


def criar_cliente_interno(dados_cliente: dict) -> dict:
    """
    Função interna para criar cliente (usada pela IA conversacional).
    Retorna os dados do cliente criado.
    """
    # Limpa o CPF/CNPJ removendo caracteres especiais
    cpf_cnpj_limpo = (
        dados_cliente["cpfCnpj"].replace(".", "").replace("-", "").replace("/", "").strip()
    )

    # Verifica se o CPF/CNPJ já existe
    cliente_existente = Cliente.query.filter_by(cpf_cnpj=cpf_cnpj_limpo).first()
    if cliente_existente:
        raise ValueError(f"CPF/CNPJ já cadastrado: {dados_cliente['cpfCnpj']}")

    cliente = Cliente(
        nome=dados_cliente["nome"].strip(),
        cpf_cnpj=cpf_cnpj_limpo,
        tipo_pessoa=dados_cliente.get("tipoPessoa") or "pessoa_fisica",
        telefone=dados_cliente["telefone"].strip(),
        email=(dados_cliente.get("email") or "").strip() or None,
        endereco=(dados_cliente.get("endereco") or "").strip() or None,
        observacoes=(dados_cliente.get("observacoes") or "").strip() or None,
        status=dados_cliente.get("status") or "ativo",
    )

    try:
        db.session.add(cliente)
        db.session.commit()

        # Criar notificações para todos os usuários após cadastrar cliente
        try:
            usuarios = Usuario.query.filter_by(ativo=True).all()
            for usuario in usuarios:
                criar_notificacao_cliente_novo(cliente, usuario.id)
            db.session.commit()
        except Exception as e:
            print(f"Aviso: Não foi possível criar notificações para novo cliente: {e}")
            db.session.rollback()  # Não afetar o cadastro do cliente

        return cliente_to_dict(cliente)

    except IntegrityError as e:
        db.session.rollback()
        error_str = str(e.orig).lower() if hasattr(e, "orig") else str(e).lower()
        if "unique constraint failed" in error_str and "cpf_cnpj" in error_str:
            raise ValueError(f"CPF/CNPJ já cadastrado: {dados_cliente['cpfCnpj']}")
        raise


@bp.get("/")
@login_required
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.criado_em.desc()).all()
    return jsonify([cliente_to_dict(c) for c in clientes])


@bp.post("/")
@login_required
def criar_cliente():
    data = request.get_json() or {}

    obrigatorios = ["nome", "cpfCnpj", "telefone"]
    if not all(data.get(c) for c in obrigatorios):
        abort(400, description="Campos obrigatórios: nome, cpfCnpj, telefone")

    # Limpa o CPF/CNPJ removendo caracteres especiais
    cpf_cnpj_limpo = (
        data["cpfCnpj"].replace(".", "").replace("-", "").replace("/", "").strip()
    )

    # Verifica se o CPF/CNPJ já existe
    cliente_existente = Cliente.query.filter_by(cpf_cnpj=cpf_cnpj_limpo).first()
    if cliente_existente:
        return (
            jsonify(
                {
                    "erro": "CPF/CNPJ já cadastrado",
                    "mensagem": f"Já existe um cliente cadastrado com o CPF/CNPJ {data['cpfCnpj']}",
                }
            ),
            409,
        )

    cliente = Cliente(
        nome=data["nome"].strip(),
        cpf_cnpj=cpf_cnpj_limpo,
        tipo_pessoa=data.get("tipoPessoa") or "pessoa_fisica",
        telefone=data["telefone"].strip(),
        email=(data.get("email") or "").strip() or None,
        endereco=(data.get("endereco") or "").strip() or None,
        observacoes=(data.get("observacoes") or "").strip() or None,
        status=data.get("status") or "ativo",
    )

    try:
        db.session.add(cliente)
        db.session.commit()

        # Criar notificações para todos os usuários após cadastrar cliente
        try:
            usuarios = Usuario.query.filter_by(ativo=True).all()
            for usuario in usuarios:
                criar_notificacao_cliente_novo(cliente, usuario.id)
            db.session.commit()
        except Exception as e:
            print(f"Aviso: Não foi possível criar notificações para novo cliente: {e}")
            db.session.rollback()  # Não afetar o cadastro do cliente

    except IntegrityError as e:
        db.session.rollback()
        # Verifica se é erro de constraint UNIQUE no CPF/CNPJ
        error_str = str(e.orig).lower() if hasattr(e, "orig") else str(e).lower()
        if "unique constraint failed" in error_str and "cpf_cnpj" in error_str:
            return (
                jsonify(
                    {
                        "erro": "CPF/CNPJ já cadastrado",
                        "mensagem": f"Já existe um cliente cadastrado com o CPF/CNPJ {data['cpfCnpj']}",
                    }
                ),
                409,
            )
        # Re-raise se for outro tipo de erro de integridade
        raise

    return jsonify(cliente_to_dict(cliente)), 201


@bp.get("/<int:cliente_id>")
@login_required
def obter_cliente(cliente_id: int):
    cliente = Cliente.query.get_or_404(cliente_id)
    return jsonify(cliente_to_dict(cliente))


@bp.delete("/<int:cliente_id>")
@login_required
def deletar_cliente(cliente_id: int):
    cliente = Cliente.query.get_or_404(cliente_id)

    # Verificar se o cliente tem ordens de serviço ativas
    from models import OrdemServico
    os_ativas = OrdemServico.query.filter_by(cliente_id=cliente_id).filter(
        OrdemServico.status.in_(["aguardando", "em_reparo", "pronto"])
    ).count()

    if os_ativas > 0:
        return (
            jsonify(
                {
                    "erro": "Cliente possui OS ativas",
                    "mensagem": f"Não é possível excluir o cliente {cliente.nome} pois ele possui {os_ativas} ordem(ns) de serviço ativa(s).",
                }
            ),
            400,
        )

    try:
        db.session.delete(cliente)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        raise

    return "", 204


@bp.put("/<int:cliente_id>")
@login_required
def atualizar_cliente(cliente_id: int):
    cliente = Cliente.query.get_or_404(cliente_id)
    data = request.get_json() or {}

    if "nome" in data:
        cliente.nome = data["nome"].strip()
    if "cpfCnpj" in data:
        cpf_cnpj_limpo = (
            data["cpfCnpj"].replace(".", "").replace("-", "").replace("/", "").strip()
        )
        # Verifica se o novo CPF/CNPJ já está sendo usado por outro cliente
        if cpf_cnpj_limpo != cliente.cpf_cnpj:
            cliente_existente = Cliente.query.filter_by(cpf_cnpj=cpf_cnpj_limpo).first()
            if cliente_existente and cliente_existente.id != cliente_id:
                return (
                    jsonify(
                        {
                            "erro": "CPF/CNPJ já cadastrado",
                            "mensagem": f"Já existe outro cliente cadastrado com o CPF/CNPJ {data['cpfCnpj']}",
                        }
                    ),
                    409,
                )
        cliente.cpf_cnpj = cpf_cnpj_limpo
    if "tipoPessoa" in data:
        cliente.tipo_pessoa = data["tipoPessoa"]
    if "telefone" in data:
        cliente.telefone = data["telefone"].strip()
    if "email" in data:
        cliente.email = (data.get("email") or "").strip() or None
    if "endereco" in data:
        cliente.endereco = (data.get("endereco") or "").strip() or None
    if "observacoes" in data:
        cliente.observacoes = (data.get("observacoes") or "").strip() or None
    if "status" in data:
        cliente.status = data["status"]

    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        # Verifica se é erro de constraint UNIQUE no CPF/CNPJ
        error_str = str(e.orig).lower() if hasattr(e, "orig") else str(e).lower()
        if "unique constraint failed" in error_str and "cpf_cnpj" in error_str:
            return (
                jsonify(
                    {
                        "erro": "CPF/CNPJ já cadastrado",
                        "mensagem": f"Já existe outro cliente cadastrado com este CPF/CNPJ",
                    }
                ),
                409,
            )
        # Re-raise se for outro tipo de erro de integridade
        raise

    return jsonify(cliente_to_dict(cliente))
