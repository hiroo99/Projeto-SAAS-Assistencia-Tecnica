from flask import (
    Flask,
    redirect,
    jsonify,
    request,
    render_template,
    send_from_directory,
)
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError

from config import get_config
from extensions import db, migrate


def create_app():
    """App factory principal."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../",
        static_url_path="/",
    )
    CORS(app)  # Enable CORS for all routes
    app.config.from_object(get_config())

    db.init_app(app)
    migrate.init_app(app, db)

    # Importa models para que o Migrate reconheça
    from models import Cliente, ProdutoEstoque, OrdemServico, Usuario  # noqa: F401

    # Cria todas as tabelas no banco de dados
    with app.app_context():
        db.create_all()

    # Blueprints
    from routes_auth import bp as auth_bp
    from routes_clientes import bp as clientes_bp
    from routes_os import bp as os_bp
    from routes_estoque import bp as estoque_bp
    from routes_notificacoes import bp as notificacoes_bp
    from routes_ai import bp as ai_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(clientes_bp, url_prefix="/api/clientes")
    app.register_blueprint(os_bp, url_prefix="/api/os")
    app.register_blueprint(estoque_bp, url_prefix="/api/estoque")
    app.register_blueprint(notificacoes_bp)
    app.register_blueprint(ai_bp, url_prefix="/api/ai")

    @app.get("/api/health")
    def health_check():
        return {"status": "ok"}

    # Rota para verificação automática de notificações
    @app.post("/api/notificacoes/verificar")
    def verificar_notificacoes():
        """Rota para verificar e criar notificações automaticamente."""
        try:
            from routes_notificacoes import verificar_e_criar_notificacoes

            verificar_e_criar_notificacoes()
            return jsonify(
                {"sucesso": True, "mensagem": "Verificação de notificações concluída"}
            )
        except Exception as e:
            print(f"Erro na verificação automática de notificações: {e}")
            return jsonify({"erro": "Erro interno do servidor"}), 500

    # Rotas para as páginas HTML
    @app.route("/")
    def index():
        return redirect("/dashboard")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/login.html")
    def login_legacy():
        return redirect("/login")

    @app.route("/atendimento")
    def atendimento():
        return render_template("atendimento.html")

    @app.route("/atendimento.html")
    def atendimento_legacy():
        return redirect("/atendimento")

    @app.route("/clientes")
    def clientes():
        return render_template("clientes.html")

    @app.route("/clientes.html")
    def clientes_legacy():
        return redirect("/clientes")

    @app.route("/estoque")
    def estoque():
        return render_template("estoque.html")

    @app.route("/estoque.html")
    def estoque_legacy():
        return redirect("/estoque")

    @app.route("/os")
    def os():
        return render_template("os.html")

    @app.route("/os.html")
    def os_legacy():
        return redirect("/os")

    @app.route("/financeiro")
    def financeiro():
        return render_template("financeiro.html")

    @app.route("/financeiro.html")
    def financeiro_legacy():
        return redirect("/financeiro")

    @app.route("/status-os")
    def status_os():
        return render_template("status_os.html")

    @app.route("/register")
    def register():
        return render_template("register.html")

    # Rota para favicon.ico
    @app.route("/favicon.ico")
    def favicon():
        try:
            return send_from_directory("../img", "favicon.png", mimetype="image/png")
        except FileNotFoundError:
            # Se não encontrar o logo, retorna uma resposta vazia
            return "", 204

    # Rota para configuração específica do Chrome DevTools (suprime logs de 404)
    @app.route("/.well-known/appspecific/com.chrome.devtools.json")
    def chrome_devtools_config():
        return "", 404

    # Error handlers globais para garantir retorno JSON nas rotas da API
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        """Trata erros de integridade do banco de dados."""
        db.session.rollback()
        # Se for uma rota da API, retorna JSON
        if request.path.startswith("/api/"):
            error_str = str(e.orig).lower() if hasattr(e, "orig") else str(e).lower()
            if "unique constraint failed" in error_str:
                campo = "campo único"
                if "cpf_cnpj" in error_str:
                    campo = "CPF/CNPJ"
                elif "codigo" in error_str:
                    campo = "código"
                elif "numero_os" in error_str:
                    campo = "número da OS"
                return (
                    jsonify(
                        {
                            "erro": "Violação de constraint único",
                            "mensagem": f"Já existe um registro com este {campo}",
                        }
                    ),
                    409,
                )
            return (
                jsonify(
                    {
                        "erro": "Erro de integridade no banco de dados",
                        "mensagem": "Não foi possível realizar a operação devido a restrições do banco de dados",
                    }
                ),
                409,
            )
        # Para outras rotas, deixa o Flask tratar normalmente
        raise

    @app.errorhandler(500)
    def handle_internal_error(e):
        """Trata erros internos do servidor."""
        # Se for uma rota da API, retorna JSON
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "erro": "Erro interno do servidor",
                        "mensagem": "Ocorreu um erro inesperado. Tente novamente mais tarde.",
                    }
                ),
                500,
            )
        # Para outras rotas, deixa o Flask tratar normalmente
        raise

    @app.errorhandler(404)
    def handle_not_found(e):
        """Trata erros 404."""
        # Se for uma rota da API, retorna JSON
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "erro": "Recurso não encontrado",
                        "mensagem": "O recurso solicitado não foi encontrado",
                    }
                ),
                404,
            )
        # Para outras rotas, deixa o Flask tratar normalmente
        raise

    @app.errorhandler(400)
    def handle_bad_request(e):
        """Trata erros 400."""
        # Se for uma rota da API, retorna JSON
        if request.path.startswith("/api/"):
            mensagem = (
                str(e.description)
                if hasattr(e, "description")
                else "Requisição inválida"
            )
            return jsonify({"erro": "Requisição inválida", "mensagem": mensagem}), 400
        # Para outras rotas, deixa o Flask tratar normalmente
        raise

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
