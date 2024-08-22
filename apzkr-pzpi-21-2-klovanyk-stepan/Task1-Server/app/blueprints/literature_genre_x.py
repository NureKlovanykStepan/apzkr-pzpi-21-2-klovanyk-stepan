from typing import Callable

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy.orm import Query

from app import Globals
from app.database.models import LiteratureGenre
from app.secret_config import SecretConfig
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.utils.extra import BlueprintsStorage
from app.services.creators.factories.body import RequestBodyFactory
from app.services.validators.base import ValidationException
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm

literature_genre_x = Blueprint(
    'literature_genre_x', __name__, url_prefix=SecretConfig().API_PREFIX+'/literature_genre_x'
)
BlueprintsStorage().register(literature_genre_x)
used_base_type = LiteratureGenre


@literature_genre_x.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@literature_genre_x.post('/')
@login_required
@permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
def create(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_create_body()()


@literature_genre_x.get('/')
@login_required
@serialization_args(request, used_base_type)
@filtering_args(request, used_base_type)
def read_all(
        serialization_modifiers: RequestArgsParser.Result,
        filtering_query_mod: Callable[[Query], Query], **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
            serialization_modifiers,
            filtering_query_mod
        )()

@literature_genre_x.get('/<genre_name>/<literature_id>')
@login_required
@serialization_args(request, used_base_type)
def read_one(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(serialization_modifiers)()


@literature_genre_x.put('/<genre_name>/<literature_id>')
@login_required
@permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
def update(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_update_body()()


@literature_genre_x.delete('/<genre_name>/<literature_id>')
@login_required
@permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
def delete(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_delete_body()()
