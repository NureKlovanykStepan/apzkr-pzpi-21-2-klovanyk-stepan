from typing import Callable

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy.orm import Query

from app import Globals
from app.database.models import Company
from app.secret_config import SecretConfig
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.utils.extra import BlueprintsStorage
from app.services.creators.factories.body import RequestBodyFactory
from app.services.processors.tools import RequestHelper
from app.services.validators.base import ValidationException
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm

companies = Blueprint('companies', __name__, url_prefix=SecretConfig().API_PREFIX+'/companies')
BlueprintsStorage().register(companies)
used_base_type = Company


@companies.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@companies.post('/')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def create(**kwargs):
    with Globals().db.session() as session:
        RequestHelper.validate_global_company_of_employee(
            RequestHelper.get_current_bound_user(session, current_user).employee
            )
        return RequestBodyFactory(session, used_base_type, request).get_crud_create_body()()


@companies.get('/')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
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

@companies.get('/<id>')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def read_one(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        RequestHelper.validate_global_company_of_employee(
            RequestHelper.get_current_bound_user(session, current_user).employee
            )

        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(serialization_modifiers)()


@companies.put('/<id>')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def update(**kwargs):
    with Globals().db.session() as session:
        RequestHelper.validate_global_company_of_employee(
            RequestHelper.get_current_bound_user(session, current_user).employee
            )
        return RequestBodyFactory(session, used_base_type, request).get_crud_update_body()()


@companies.delete('/<id>')
@login_required
@permissions_of_employee_required(current_user, Perm.HEAD_MANAGER)
def delete(**kwargs):
    with Globals().db.session() as session:
        RequestHelper.validate_global_company_of_employee(
            RequestHelper.get_current_bound_user(session, current_user).employee
            )
        return RequestBodyFactory(session, used_base_type, request).get_crud_delete_body()()


@companies.get('/me')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.NONE)
def read_self(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        request.view_args['id'] = RequestHelper.get_current_bound_user(
            session, current_user
        ).employee.establishment.company_id
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(serialization_modifiers)()


@companies.get('/accessible')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.NONE)
def read_accessible(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        current_bound_user = RequestHelper.get_current_bound_user(session, current_user)
        current_company = RequestHelper.get_company_of_employee(current_bound_user.employee)
        if not current_company.global_access_company:
            query_mod = lambda query: query.where(Company.id == current_company.id)
        else:
            query_mod = lambda query: query
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(serialization_modifiers, query_mod)()