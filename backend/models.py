from datetime import datetime

from extensions import db


class TimestampMixin:
    criado_em = db.Column(db.DateTime, default=datetime.now)
    atualizado_em = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )


class Cliente(TimestampMixin, db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, index=True)
    cpf_cnpj = db.Column(db.String(14), nullable=False, unique=True)
    tipo_pessoa = db.Column(db.String(20), nullable=False, default="pessoa_fisica")
    endereco = db.Column(db.String(200))
    email = db.Column(db.String(120), index=True)
    telefone = db.Column(db.String(20), nullable=False)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="ativo", index=True)

    ordens_servico = db.relationship(
        "OrdemServico", back_populates="cliente", cascade="all, delete-orphan"
    )


class ProdutoEstoque(TimestampMixin, db.Model):
    __tablename__ = "produtos_estoque"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False, unique=True)
    nome = db.Column(db.String(150), nullable=False, index=True)
    categoria = db.Column(db.String(50), nullable=False, index=True)
    descricao = db.Column(db.Text)
    quantidade = db.Column(db.Integer, nullable=False, default=0, index=True)
    estoque_minimo = db.Column(db.Integer, nullable=False, default=0)
    preco_custo = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    preco_venda = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    fornecedor = db.Column(db.String(150))
    localizacao = db.Column(db.String(100))


class OrdemServico(TimestampMixin, db.Model):
    __tablename__ = "ordens_servico"

    id = db.Column(db.Integer, primary_key=True)
    numero_os = db.Column(db.String(20), nullable=False, unique=True, index=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False, index=True)
    cliente = db.relationship("Cliente", back_populates="ordens_servico")

    tipo_aparelho = db.Column(db.String(50), nullable=False)
    marca_modelo = db.Column(db.String(100), nullable=False)
    imei_serial = db.Column(db.String(100))
    cor_aparelho = db.Column(db.String(50))

    problema_relatado = db.Column(db.String(400), nullable=False)
    diagnostico_tecnico = db.Column(db.String(400))

    prazo_estimado = db.Column(db.Integer, nullable=False, default=3)
    valor_orcamento = db.Column(db.Numeric(10, 2))

    status = db.Column(
        db.String(20),
        nullable=False,
        default="aguardando",  # aguardando, em_reparo, pronto, entregue, cancelado
        index=True
    )
    prioridade = db.Column(
        db.String(20),
        nullable=False,
        default="normal",  # baixa, normal, alta, urgente
    )

    observacoes = db.Column(db.Text)


class Usuario(TimestampMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True)
    ativo = db.Column(db.Boolean, default=True)

    # Relacionamento com notificações
    notificacoes = db.relationship(
        "Notificacao", back_populates="usuario", cascade="all, delete-orphan"
    )


class Notificacao(TimestampMixin, db.Model):
    __tablename__ = "notificacoes"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False, index=True)  # os_atrasada, estoque_critico, etc.
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    dados_referencia = db.Column(db.JSON)  # Dados para link/ação (ex: {"os_id": 123})
    lida = db.Column(db.Boolean, default=False, index=True)
    prioridade = db.Column(db.String(20), default="normal")  # baixa, normal, alta, urgente

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    usuario = db.relationship("Usuario", back_populates="notificacoes")
