from importlib import import_module
from pathlib import Path

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import create_database, database_exists

from . import Globals
from .database.models import Base
from .secret_config import SecretConfig
from app.utils.file_manager.files import FileManager
from .utils.extra import SecondaryConfig, BlueprintsStorage


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(SecretConfig())
    app.config.from_object(SecondaryConfig.FlaskAppConfig)
    Globals(app)
    CORS(
        app, supports_credentials=True, resources={r"/*": {"origins": "*"}}, expose_headers=['Content-Disposition']
    )
    FileManager(Path(app.root_path) / SecretConfig().UPLOAD_FOLDER)

    with app.app_context():
        if not database_exists(Globals().db.engine.url):
            create_database(Globals().db.engine.url)
        create_db_tables(Globals().db.engine)

    register_blueprints(app)

    return app


def create_db_tables(engine: SQLAlchemy.engine) -> None:
    Base.metadata.create_all(engine)


def register_blueprints(app: Flask) -> None:
    blueprints = SecondaryConfig().BLUEPRINTS_PATH.iterdir()
    blueprints = [bp for bp in blueprints if bp.is_file() and bp.suffix == '.py' and bp.stem != '__init__']
    [import_module(f'app.blueprints.{bp.stem}') for bp in blueprints]
    blueprints_storage = BlueprintsStorage()
    for blueprint in blueprints_storage.blueprints:
        app.register_blueprint(blueprint)
