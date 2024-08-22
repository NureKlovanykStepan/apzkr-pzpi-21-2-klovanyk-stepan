from http import HTTPStatus

from flask import Blueprint, request
from flask_login import login_user, logout_user, login_required

from app import Globals
from app.database.models import User
from app.secret_config import SecretConfig
from app.utils.extra import BlueprintsStorage
from app.services.validators.auth import AuthGeneralValidator
from app.services.validators.base import ValidationException

auth = Blueprint('auth', __name__, url_prefix=SecretConfig().API_PREFIX+'/auth')
BlueprintsStorage().register(auth)
login_manager = Globals().login_manager


@auth.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@login_manager.user_loader
def user_loader(user_id):
    with Globals().db.session() as session:
        return session.get(User, user_id)


@auth.post('/login')
def user_login():
    def on_success(user: User):
        login_user(user)

    validator = AuthGeneralValidator(on_success)
    validator.validate(request)

    return "Login success", HTTPStatus.OK


@auth.get('/logout')
@login_required
def user_logout():
    logout_user()
    return "Logout success", HTTPStatus.OK
