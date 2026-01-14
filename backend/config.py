import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuração básica da aplicação Flask."""

    # Em desenvolvimento, usamos SQLite local.
    # Em produção, defina a variável de ambiente DATABASE_URL
    # Ex: mysql+pymysql://user:senha@localhost/assistencia_tecnica
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "mude-esta-chave-em-producao")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = dict(
    development=DevelopmentConfig,
    production=ProductionConfig,
)


def get_config():
    env = os.getenv("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
