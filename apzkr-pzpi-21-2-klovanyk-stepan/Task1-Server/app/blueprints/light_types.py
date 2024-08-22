from typing import Callable

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy.orm import Query

from app import Globals
from app.database.models import LightType
from app.secret_config import SecretConfig
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.utils.extra import BlueprintsStorage
from app.services.creators.factories.body import RequestBodyFactory
from app.services.validators.base import ValidationException
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm

light_types = Blueprint('light_types', __name__, url_prefix=SecretConfig().API_PREFIX+'/light_types')
BlueprintsStorage().register(light_types)
used_base_type = LightType


@light_types.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@light_types.post('/')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def create(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_create_body()()


@light_types.get('/')
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

@light_types.get('/<name>')
@login_required
@serialization_args(request, used_base_type)
def read_one(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(serialization_modifiers)()


@light_types.put('/<name>')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def update(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_update_body()()


@light_types.delete('/<name>')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def delete(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_delete_body()()
