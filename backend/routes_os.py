from datetime import datetime, timedelta

from flask import Blueprint, abort, jsonify, request

from extensions import db
from models import Cliente, OrdemServico, Usuario
from auth_utils import login_required
from routes_notificacoes import criar_notificacao_os_pronta
from ai_utils import gerar_resumo

bp = Blueprint("os", __name__)


def os_to_dict(os_obj: OrdemServico, incluir_cliente: bool = True) -> dict:
    data_criacao = os_obj.criado_em or datetime.utcnow()
    prazo_estimado = os_obj.prazo_estimado or 3
    prazo_limite = data_criacao + timedelta(days=prazo_estimado)

    base = {
        "id": os_obj.id,
        "numeroOS": os_obj.numero_os,
        "clienteId": os_obj.cliente_id,
        "tipoAparelho": os_obj.tipo_aparelho,
        "marcaModelo": os_obj.marca_modelo,
        "imeiSerial": os_obj.imei_serial,
        "corAparelho": os_obj.cor_aparelho,
        "problemaRelatado": os_obj.problema_relatado,
        "diagnosticoTecnico": os_obj.diagnostico_tecnico,
        "prazoEstimado": os_obj.prazo_estimado,
        "valorOrcamento": float(os_obj.valor_orcamento or 0),
        "status": os_obj.status,
        "prioridade": os_obj.prioridade,
        "observacoes": os_obj.observacoes,
        "dataCriacao": data_criacao.isoformat(),
        "dataAtualizacao": (os_obj.atualizado_em or data_criacao).isoformat(),
        "prazoLimite": prazo_limite.isoformat(),
    }

    if incluir_cliente and os_obj.cliente:
        base["clienteNome"] = os_obj.cliente.nome

    return base


def gerar_proximo_numero_os() -> str:
    ultimo = (
        OrdemServico.query.order_by(OrdemServico.id.desc()).with_entities(
            OrdemServico.numero_os
        )
    ).first()
    if not ultimo or not ultimo[0]:
        return "#OS0001"

    numero = ultimo[0].replace("#", "").replace("OS", "")
    try:
        prox = int(numero) + 1
    except ValueError:
        prox = 1
    return f"#OS{prox:04d}"


@bp.get("/")
@login_required
def listar_os():
    ordens = (
        OrdemServico.query.order_by(OrdemServico.criado_em.desc()).join(Cliente).all()
    )
    return jsonify([os_to_dict(o) for o in ordens])


@bp.post("/")
@login_required
def criar_os():
    data = request.get_json() or {}

    obrigatorios = ["clienteId", "tipoAparelho", "marcaModelo", "problemaRelatado"]
    if not all(data.get(c) for c in obrigatorios):
        abort(
            400,
            description=(
                "Campos obrigatórios: clienteId, tipoAparelho, "
                "marcaModelo, problemaRelatado"
            ),
        )

    cliente = Cliente.query.get(data["clienteId"])
    if not cliente:
        abort(400, description="Cliente não encontrado")

    os_obj = OrdemServico(
        numero_os=gerar_proximo_numero_os(),
        cliente=cliente,
        tipo_aparelho=data["tipoAparelho"],
        marca_modelo=data["marcaModelo"],
        imei_serial=data.get("imeiSerial"),
        cor_aparelho=data.get("corAparelho"),
        problema_relatado=data["problemaRelatado"],
        diagnostico_tecnico=data.get("diagnosticoTecnico"),
        prazo_estimado=int(data.get("prazoEstimado") or 3),
        valor_orcamento=data.get("valorOrcamento") or None,
        status=data.get("status") or "aguardando",
        prioridade=data.get("prioridade") or "normal",
        observacoes=data.get("observacoes"),
    )

    db.session.add(os_obj)
    db.session.commit()

    # Tentar gerar resumo automático usando IA
    try:
        resumo_ia = gerar_resumo(data["problemaRelatado"])
        # Atualizar observações com o resumo da IA se não houver observações
        if not os_obj.observacoes:
            os_obj.observacoes = f"[IA] Resumo: {resumo_ia}"
            db.session.commit()
    except Exception as e:
        print(f"Aviso: Não foi possível gerar resumo automático: {e}")
        # Não afeta a criação da OS se a IA falhar

    return jsonify(os_to_dict(os_obj)), 201


@bp.get("/<int:os_id>")
@login_required
def obter_os(os_id: int):
    os_obj = OrdemServico.query.get_or_404(os_id)
    return jsonify(os_to_dict(os_obj))


@bp.put("/<int:os_id>")
@login_required
def atualizar_os(os_id: int):
    os_obj = OrdemServico.query.get_or_404(os_id)
    data = request.get_json() or {}

    # Verificar se o status está sendo alterado para "pronto"
    status_anterior = os_obj.status
    novo_status = data.get("status")

    if "clienteId" in data:
        cliente = Cliente.query.get(data["clienteId"])
        if not cliente:
            abort(400, description="Cliente não encontrado")
        os_obj.cliente = cliente

    for campo_api, attr in [
        ("tipoAparelho", "tipo_aparelho"),
        ("marcaModelo", "marca_modelo"),
        ("imeiSerial", "imei_serial"),
        ("corAparelho", "cor_aparelho"),
        ("problemaRelatado", "problema_relatado"),
        ("diagnosticoTecnico", "diagnostico_tecnico"),
        ("observacoes", "observacoes"),
        ("status", "status"),
        ("prioridade", "prioridade"),
    ]:
        if campo_api in data:
            setattr(os_obj, attr, data[campo_api])

    if "prazoEstimado" in data:
        os_obj.prazo_estimado = int(data["prazoEstimado"])
    if "valorOrcamento" in data:
        os_obj.valor_orcamento = data["valorOrcamento"]

    db.session.commit()

    # Criar notificação se o status mudou para "pronto"
    if status_anterior != "pronto" and novo_status == "pronto":
        try:
            usuarios = Usuario.query.filter_by(ativo=True).all()
            for usuario in usuarios:
                criar_notificacao_os_pronta(os_obj, usuario.id)
            db.session.commit()
        except Exception as e:
            print(f"Aviso: Não foi possível criar notificações para OS pronta: {e}")
            db.session.rollback()  # Não afetar a atualização da OS

    return jsonify(os_to_dict(os_obj))


@bp.delete("/<int:os_id>")
@login_required
def deletar_os(os_id: int):
    os_obj = OrdemServico.query.get_or_404(os_id)
    db.session.delete(os_obj)
    db.session.commit()
    return "", 204


@bp.get("/status/<numero_os>")
def consultar_status_os_publico(numero_os: str):
    """Rota pública para consulta de status da OS por clientes."""
    os_obj = OrdemServico.query.filter_by(numero_os=numero_os).first()
    if not os_obj:
        return (
            jsonify(
                {
                    "erro": "OS não encontrada",
                    "mensagem": f"Não foi encontrada uma ordem de serviço com o número {numero_os}",
                }
            ),
            404,
        )

    # Retorna dados públicos da OS
    return jsonify(
        {
            "numeroOS": os_obj.numero_os,
            "status": os_obj.status,
            "clienteNome": (
                os_obj.cliente.nome if os_obj.cliente else "Cliente não informado"
            ),
            "tipoAparelho": os_obj.tipo_aparelho,
            "marcaModelo": os_obj.marca_modelo,
            "problemaRelatado": os_obj.problema_relatado,
            "diagnosticoTecnico": os_obj.diagnostico_tecnico,
            "prazoEstimado": os_obj.prazo_estimado,
            "valorOrcamento": float(os_obj.valor_orcamento or 0),
            "dataCriacao": os_obj.criado_em.isoformat() if os_obj.criado_em else None,
            "dataAtualizacao": (
                os_obj.atualizado_em.isoformat() if os_obj.atualizado_em else None
            ),
            "prazoLimite": (
                (os_obj.criado_em + timedelta(days=os_obj.prazo_estimado)).isoformat()
                if os_obj.criado_em
                else None
            ),
        }
    )
