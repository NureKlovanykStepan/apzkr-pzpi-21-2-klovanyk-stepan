from http import HTTPStatus
from typing import Callable

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy.orm import Query

from app import Globals
from app.database.models import User
from app.secret_config import SecretConfig
from app.utils.extra import BlueprintsStorage
from app.services.creators.factories.body import RequestBodyFactory
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm
from app.services.processors.tools import RequestHelper
from app.services.validators.base import ValidationException, ValidationExceptionType
from app.services.validators.crud import UpdateValidationResult, ReadOrDeleteValidationResult

users = Blueprint('users', __name__, url_prefix=SecretConfig().API_PREFIX + '/users')
BlueprintsStorage().register(users)
used_base_type = User


@users.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@users.post('/')
def create(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_create_body()()


@users.get('/')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
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


@users.get('/<email>')
@login_required
@serialization_args(request, used_base_type)
def read_one(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(serialization_modifiers)()


@users.put('/<email>')
@login_required
def update(**kwargs):
    with Globals().db.session() as session:
        def validate_self(result: UpdateValidationResult):
            user_to_update: User = result.object_to_update
            if user_to_update.email != current_user.email:
                raise ValidationException(ValidationExceptionType.NOT_ENOUGH_PERMISSIONS, HTTPStatus.BAD_REQUEST)

        return RequestBodyFactory(session, used_base_type, request, validate_self).get_crud_update_body()()


@users.delete('/<email>')
@login_required
def delete(**kwargs):
    with Globals().db.session() as session:
        def validate_requestor(result: ReadOrDeleteValidationResult):
            user_to_delete: User = result.object
            current_bound_user: User = RequestHelper.get_current_bound_user(session, current_user)
            if (not (current_employee := current_bound_user.employee)
                    and not user_to_delete.email == current_bound_user.email):
                raise ValidationException(ValidationExceptionType.NOT_ENOUGH_PERMISSIONS, HTTPStatus.BAD_REQUEST)
            if not RequestHelper.get_company_of_employee(current_employee).global_access_company:
                raise ValidationException(ValidationExceptionType.NOT_ENOUGH_PERMISSIONS, HTTPStatus.BAD_REQUEST)
            if not current_employee.head_manager:
                raise ValidationException(ValidationExceptionType.NOT_ENOUGH_PERMISSIONS, HTTPStatus.BAD_REQUEST)

        return RequestBodyFactory(session, used_base_type, request, validate_requestor).get_crud_delete_body()()


@users.get('/self')
@login_required
@serialization_args(request, used_base_type)
def read_self(serialization_modifiers: RequestArgsParser.Result, **kwargs):
    with Globals().db.session() as session:
        serializer = RequestHelper.get_general_serializer(
            RequestHelper.get_current_bound_user(session, current_user),
            serialization_modifiers,
            current_user,
            session
        )
        return serializer.serialize()
