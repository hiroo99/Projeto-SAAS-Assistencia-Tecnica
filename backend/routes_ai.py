from flask import Blueprint, jsonify, request

from ai_utils import gerar_pre_diagnostico, gerar_resumo
from auth_utils import login_required

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
