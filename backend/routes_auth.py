from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from extensions import db
from models import Usuario
from auth_utils import autenticar_usuario, gerar_token_jwt, login_required

bp = Blueprint("auth", __name__)


@bp.post("/login")
def login():
    """Endpoint para login de usuários."""
    data = request.get_json() or {}

    usuario = data.get("usuario", "").strip()
    senha = data.get("senha", "")

    if not usuario or not senha:
        return jsonify({
            "erro": "Dados inválidos",
            "mensagem": "Usuário e senha são obrigatórios"
        }), 400

    # Autentica o usuário
    user = autenticar_usuario(usuario, senha)

    if not user:
        return jsonify({
            "erro": "Credenciais inválidas",
            "mensagem": "Usuário ou senha incorretos"
        }), 401

    # Gera token JWT
    token = gerar_token_jwt(user.id, user.usuario)

    return jsonify({
        "token": token,
        "usuario": {
            "id": user.id,
            "usuario": user.usuario,
            "nome": user.nome,
            "email": user.email
        },
        "mensagem": "Login realizado com sucesso"
    }), 200


@bp.post("/register")
def register():
    """Endpoint para registro de novos usuários (apenas para desenvolvimento)."""
    data = request.get_json() or {}

    # Campos obrigatórios
    obrigatorios = ["usuario", "senha"]
    if not all(data.get(c) for c in obrigatorios):
        return jsonify({
            "erro": "Dados inválidos",
            "mensagem": "Usuário e senha são obrigatórios"
        }), 400

    # Verifica se usuário já existe
    if Usuario.query.filter_by(usuario=data["usuario"]).first():
        return jsonify({
            "erro": "Usuário já existe",
            "mensagem": "Este nome de usuário já está em uso"
        }), 409

    # Verifica se CPF já existe
    import re
    cpf_limpo = re.sub(r'\D', '', data.get("cpf", "")) if data.get("cpf") else ""
    if cpf_limpo and Usuario.query.filter_by(cpf=cpf_limpo).first():
        return jsonify({
            "erro": "CPF já existe",
            "mensagem": "Este CPF já está cadastrado"
        }), 409

    # Verifica se email já existe (se fornecido)
    if data.get("email") and Usuario.query.filter_by(email=data["email"]).first():
        return jsonify({
            "erro": "Email já existe",
            "mensagem": "Este email já está cadastrado"
        }), 409

    # Cria novo usuário
    user = Usuario(
        usuario=data["usuario"].strip(),
        senha_hash=generate_password_hash(data["senha"]),
        nome=(data.get("nome") or "").strip() or None,
        cpf=cpf_limpo or None,
        telefone=(data.get("telefone") or "").strip() or None,
        email=(data.get("email") or "").strip() or None,
        ativo=True
    )

    db.session.add(user)
    db.session.commit()

    # Gera token JWT para o novo usuário
    token = gerar_token_jwt(user.id, user.usuario)

    return jsonify({
        "token": token,
        "usuario": {
            "id": user.id,
            "usuario": user.usuario,
            "nome": user.nome,
            "email": user.email
        },
        "mensagem": "Usuário registrado com sucesso"
    }), 201


@bp.get("/me")
@login_required
def get_current_user():
    """Endpoint para obter informações do usuário atual."""
    from auth_utils import get_usuario_atual

    usuario_atual = get_usuario_atual()
    if not usuario_atual:
        return jsonify({
            "erro": "Não autenticado",
            "mensagem": "Token de autenticação necessário"
        }), 401

    # Busca usuário completo no banco
    user = Usuario.query.get(usuario_atual["id"])
    if not user:
        return jsonify({
            "erro": "Usuário não encontrado",
            "mensagem": "O usuário associado ao token não foi encontrado"
        }), 404

    return jsonify({
        "id": user.id,
        "usuario": user.usuario,
        "nome": user.nome,
        "cpf": user.cpf,
        "telefone": user.telefone,
        "email": user.email,
        "ativo": user.ativo,
        "dataCadastro": user.criado_em.isoformat() if user.criado_em else None
    }), 200


@bp.put("/me")
@login_required
def update_current_user():
    """Endpoint para atualizar informações do usuário atual."""
    from auth_utils import get_usuario_atual

    usuario_atual = get_usuario_atual()
    if not usuario_atual:
        return jsonify({
            "erro": "Não autenticado",
            "mensagem": "Token de autenticação necessário"
        }), 401

    # Busca usuário completo no banco
    user = Usuario.query.get(usuario_atual["id"])
    if not user:
        return jsonify({
            "erro": "Usuário não encontrado",
            "mensagem": "O usuário associado ao token não foi encontrado"
        }), 404

    data = request.get_json() or {}

    # Validações - apenas senha pode ser alterada
    if not data or "senha" not in data:
        return jsonify({
            "erro": "Dados inválidos",
            "mensagem": "Apenas a senha pode ser alterada no perfil"
        }), 400

    # Atualiza senha
    senha = data["senha"]
    if not senha or len(senha) < 6:
        return jsonify({
            "erro": "Senha inválida",
            "mensagem": "A senha deve ter pelo menos 6 caracteres"
        }), 400
    user.senha_hash = generate_password_hash(senha)

    # Salva alterações
    db.session.commit()

    return jsonify({
        "id": user.id,
        "usuario": user.usuario,
        "nome": user.nome,
        "email": user.email,
        "ativo": user.ativo,
        "dataCadastro": user.criado_em.isoformat() if user.criado_em else None,
        "mensagem": "Perfil atualizado com sucesso"
    }), 200
