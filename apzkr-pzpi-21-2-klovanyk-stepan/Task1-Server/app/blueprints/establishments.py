from typing import Callable

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy.orm import Query

from app import Globals
from app.database.models import Establishment, Employee
from app.secret_config import SecretConfig
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.utils.extra import BlueprintsStorage
from app.services.creators.factories.body import RequestBodyFactory
from app.services.processors.tools import RequestHelper
from app.services.validators.base import ValidationException
from app.services.validators.crud import CreateValidationResult, ReadOrDeleteValidationResult, UpdateValidationResult
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm

establishments = Blueprint('establishments', __name__, url_prefix=SecretConfig().API_PREFIX + '/establishments')
BlueprintsStorage().register(establishments)
used_base_type = Establishment


@establishments.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@establishments.post('/')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def create(**kwargs):
    with Globals().db.session() as session:
        def validation_extension(result: CreateValidationResult):
            requestor_employee: Employee = RequestHelper.get_current_bound_user(session, current_user).employee
            RequestHelper.validate_same_company_or_global(
                requestor_employee, result.object_to_create.company_id
            )

        return RequestBodyFactory(session, used_base_type, request).get_crud_create_body(validation_extension)()


@establishments.get('/')
@login_required
@serialization_args(request, used_base_type)
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


@establishments.get('/<id>')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def read_one(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        def validation_extension(result: ReadOrDeleteValidationResult):
            requestor_employee: Employee = RequestHelper.get_current_bound_user(session, current_user).employee
            RequestHelper.validate_same_company_or_global(
                requestor_employee, result.object.company_id
            )

        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(
            serialization_modifiers, validation_extension
        )()


@establishments.get('/forCompany/<company_id>')
@login_required
@permissions_of_employee_required(current_user, Perm.NONE)
@serialization_args(request, Employee)
def get_establishments_for_company(
        company_id: int,
        serialization_modifiers: RequestArgsParser.Result
):
    with Globals().db.session() as session:
        requesting_employee = RequestHelper.get_current_bound_user(session, current_user).employee
        if int(company_id) != requesting_employee.establishment.company_id:
            RequestHelper.validate_global_company_of_employee(requesting_employee)
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
            serialization_modifiers,
            lambda query: query.where(Establishment.company_id == company_id)
        )()


@establishments.get('/my')
@login_required
@permissions_of_employee_required(current_user, Perm.NONE)
@serialization_args(request, Employee)
def get_my_establishments_request(
        serialization_modifiers: RequestArgsParser.Result
):
    with Globals().db.session() as session:
        my_company = RequestHelper.get_company_of_employee(
            RequestHelper.get_current_bound_user(
                session, current_user
            ).employee
        )

        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
            serialization_modifiers, lambda query: query.where(
                Establishment.company_id == my_company.id
            )
        )()


@establishments.put('/<id>')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def update(**kwargs):
    with Globals().db.session() as session:
        def validation_extension(result: UpdateValidationResult):
            requestor_employee: Employee = RequestHelper.get_current_bound_user(session, current_user).employee
            RequestHelper.validate_same_company_or_global(
                requestor_employee,
                result.object_to_update.company_id
            )
            if result.object_new_data.get("company_id"):
                RequestHelper.validate_same_company_or_global(
                    requestor_employee, session.get(
                        Establishment, result.object_new_data["company_id"]
                    )
                )

        return RequestBodyFactory(session, used_base_type, request).get_crud_update_body(validation_extension)()


@establishments.delete('/<id>')
@login_required
@permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
def delete(**kwargs):
    with Globals().db.session() as session:
        def validation_extension(result: ReadOrDeleteValidationResult):
            requestor_employee: Employee = RequestHelper.get_current_bound_user(session, current_user).employee
            RequestHelper.validate_same_company_or_global(requestor_employee, result.object.company_id)

        return RequestBodyFactory(session, used_base_type, request).get_crud_delete_body(validation_extension)()
