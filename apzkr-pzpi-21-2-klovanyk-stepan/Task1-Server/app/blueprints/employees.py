from typing import Callable

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy import and_
from sqlalchemy.orm import Query

from app import Globals
from app.database.models import Employee, Establishment
from app.secret_config import SecretConfig
from app.utils.extra import BlueprintsStorage
from app.services.creators.factories.body import RequestBodyFactory
from app.services.processors.tools import RequestHelper
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm
from app.services.validators.base import ValidationException
from app.services.validators.crud import (CreateValidationResult, ReadOrDeleteValidationResult,
                                          UpdateValidationResult)

employees = Blueprint('employees', __name__, url_prefix=SecretConfig().API_PREFIX + '/employees')
BlueprintsStorage().register(employees)

used_base_type = Employee


@employees.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@employees.post('/')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def create_employee_request(**kwargs):
    with Globals().db.session() as session:
        def validation_extension(result: CreateValidationResult):
            requestor_employee: Employee = RequestHelper.get_current_bound_user(session, current_user).employee
            RequestHelper.validate_same_company_or_global(
                requestor_employee, session.get(Establishment, result.object_to_create.establishment_id).company_id
            )

        return RequestBodyFactory(session, used_base_type, request).get_crud_create_body(validation_extension)()


@employees.get('/')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
@serialization_args(request, Employee)
@filtering_args(request, used_base_type)
def read_all(
        serialization_modifiers: RequestArgsParser.Result,
        filtering_query_mod: Callable[[Query], Query], **kwargs
):
    with Globals().db.session() as session:
        RequestHelper.validate_global_company_of_employee(
            RequestHelper.get_current_bound_user(session, current_user).employee
        )
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
            serialization_modifiers,
            filtering_query_mod
        )()


@employees.get('/<user_email>')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
@serialization_args(request, Employee)
def get_employee_request(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        def validation_extension(result: ReadOrDeleteValidationResult):
            requestor_employee: Employee = RequestHelper.get_current_bound_user(session, current_user).employee
            RequestHelper.validate_same_company_or_global(requestor_employee, result.object.establishment.company_id)

        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(
            serialization_modifiers, validation_extension
        )()


@employees.get('/my')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
@serialization_args(request, Employee)
def get_my_employee_request(
        serialization_modifiers: RequestArgsParser.Result
):
    with Globals().db.session() as session:
        my_company = RequestHelper.get_company_of_employee(
            RequestHelper.get_current_bound_user(
                session, current_user
            ).employee
        )

        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
            serialization_modifiers, lambda query: query.join(
                Establishment, and_(
                    Establishment.id == Employee.establishment_id, Establishment.company_id == my_company.id
                )
            )
        )()


@employees.put('/<user_email>')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def update_employee_request(**kwargs):
    with Globals().db.session() as session:
        def validation_extension(result: UpdateValidationResult):
            requestor_employee: Employee = RequestHelper.get_current_bound_user(session, current_user).employee
            RequestHelper.validate_same_company_or_global(
                requestor_employee, result.object_to_update.establishment.company_id
            )
            if result.object_new_data.get("establishment_id"):
                RequestHelper.validate_same_company_or_global(
                    requestor_employee, session.get(
                        Establishment, result.object_new_data["establishment_id"]
                    )
                )

        return RequestBodyFactory(session, used_base_type, request).get_crud_update_body(validation_extension)()


@employees.delete('/<user_email>')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def delete_employee_request(**kwargs):
    with (Globals().db.session() as session):
        def validation_extension(result: ReadOrDeleteValidationResult):
            requestor_employee: Employee = RequestHelper.get_current_bound_user(session, current_user).employee
            RequestHelper.validate_same_company_or_global(requestor_employee, result.object.establishment.company_id)

        return RequestBodyFactory(session, used_base_type, request).get_crud_delete_body(validation_extension)()
