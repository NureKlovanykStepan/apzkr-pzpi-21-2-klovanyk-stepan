from flask import Blueprint, request, current_app
from sqlalchemy_utils import create_database, drop_database

from app import Globals
from app.database.models import Base
from app.secret_config import SecretConfig
from app.utils.extra import BlueprintsStorage
from app.utils.mocker import MockStation

utils_debug = Blueprint('DEBUG', __name__, url_prefix=SecretConfig().API_PREFIX + '/DEBUG')
BlueprintsStorage().register(utils_debug)


@utils_debug.get('mock_db_basic')
def mock_basic_relations():
    assert current_app.debug
    Globals().db.session.add_all(MockStation.BasicWithRelations())
    Globals().db.session.commit()
    return '', 200


@utils_debug.get('clear_db')
def clear_db():
    assert current_app.debug
    Base.metadata.drop_all(Globals().db.engine)
    Base.metadata.create_all(Globals().db.engine)
    return '', 200


@utils_debug.get('check_args/<id>/<name>')
def check_args(id: int, name: str):
    assert current_app.debug
    return [request.args, request.view_args, request.args.getlist("G")], 200


@utils_debug.get('recreate_db')
def recreate_db():
    assert current_app.debug
    drop_database(Globals().db.engine.url)
    create_database(Globals().db.engine.url)
    Base.metadata.create_all(Globals().db.engine)
    return '', 200
