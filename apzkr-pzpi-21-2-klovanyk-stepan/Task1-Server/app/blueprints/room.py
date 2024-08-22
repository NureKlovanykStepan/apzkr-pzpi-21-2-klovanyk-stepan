from typing import Callable

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy.orm import Query

from app import Globals
from app.database.models import Room
from app.secret_config import SecretConfig
from app.utils.extra import BlueprintsStorage
from app.services.creators.factories.body import RequestBodyFactory
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm
from app.services.validators.base import ValidationException

rooms = Blueprint(
    'rooms',
    __name__,
    url_prefix=SecretConfig().API_PREFIX + '/rooms'
)
BlueprintsStorage().register(
    rooms
)
used_base_type = Room


@rooms.errorhandler(
    ValidationException
)
def validation_exception_handler(validation_exception: ValidationException):
    return str(
        validation_exception
    ), validation_exception.http_status_code


@rooms.post(
    '/'
)
@login_required
@permissions_of_employee_required(
    current_user,
    Perm.IOT_MANAGER
)
def create(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(
            session,
            used_base_type,
            request
        ).get_crud_create_body()()


@rooms.get(
    '/'
)
@login_required
@serialization_args(
    request,
    used_base_type
)
@permissions_of_employee_required(
    current_user,
    Perm.BOOKING_MANAGER
)
@filtering_args(
    request,
    used_base_type
)
def read_all(
        serialization_modifiers: RequestArgsParser.Result,
        filtering_query_mod: Callable[[Query], Query], **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(
            session,
            used_base_type,
            request
        ).get_crud_read_many_body(
            serialization_modifiers,
            filtering_query_mod
        )()


@rooms.get(
    '/<id>'
)
@login_required
@serialization_args(
    request,
    used_base_type
)
@permissions_of_employee_required(
    current_user,
    Perm.BOOKING_MANAGER
)
def read_one(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(
            session,
            used_base_type,
            request
        ).get_crud_read_single_body(
            serialization_modifiers
        )()


@rooms.get(
    '/forEstablishment/<establishment_id>'
)
@login_required
@serialization_args(
    request,
    used_base_type
)
@permissions_of_employee_required(
    current_user,
    Perm.BOOKING_MANAGER
)
def read_by_establishment(
        serialization_modifiers: RequestArgsParser.Result, establishment_id: int, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(
            session,
            used_base_type,
            request
        ).get_crud_read_many_body(
            serialization_modifiers,
            lambda query: query.where(
                Room.establishment_id == establishment_id
            )
        )()


@rooms.put(
    '/<id>'
)
@login_required
@permissions_of_employee_required(
    current_user,
    Perm.IOT_MANAGER
)
def update(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(
            session,
            used_base_type,
            request
        ).get_crud_update_body()()


@rooms.delete(
    '/<id>'
)
@login_required
@permissions_of_employee_required(
    current_user,
    Perm.IOT_MANAGER
)
def delete(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(
            session,
            used_base_type,
            request
        ).get_crud_delete_body()()
