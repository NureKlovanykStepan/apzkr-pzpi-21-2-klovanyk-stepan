from typing import Callable

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy.orm import Query

from app import Globals
from app.database.models import UserBooking
from app.secret_config import SecretConfig
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.utils.extra import BlueprintsStorage
from app.services.creators.factories.body import RequestBodyFactory
from app.services.validators.base import ValidationException
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm

user_booking_x = Blueprint(
    'user_booking_x', __name__, url_prefix=SecretConfig().API_PREFIX+'/user_booking_x'
)
BlueprintsStorage().register(user_booking_x)
used_base_type = UserBooking


@user_booking_x.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@user_booking_x.post('/')
@login_required
@permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
def create(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_create_body()()


@user_booking_x.get('/')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
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

@user_booking_x.get('/<user_email>/<booking_id>')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
def read_one(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(serialization_modifiers)()


@user_booking_x.put('/<user_email>/<booking_id>')
@login_required
@permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
def update(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_update_body()()


@user_booking_x.delete('/<user_email>/<booking_id>')
@login_required
@permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
def delete(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_delete_body()()
