from app.database.models import Country
from app.utils.extra import DefaultExtraValidators
from app.services.creators.builders.buieprints import BlueprintDefaults
from app.services.creators.builders.routes import RequestModifiers
from app.services.decorators.general.permissions import RequiredPermissionsFlag

#
# countries = Blueprint('countries', __name__, url_prefix=SecretConfig().API_PREFIX + '/countries')
# BlueprintsStorage().register(countries)
# used_base_type = Country


# @countries.errorhandler(ValidationException)
# def validation_exception_handler(validation_exception: ValidationException):
#     return str(validation_exception), validation_exception.http_status_code
#
#
# @countries.post('/')
# @login_required
# @permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
# def create_country(**kwargs):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).get_crud_create_body()()
#
#
# @countries.get('/')
# @serialization_args(request, used_base_type)
# @filtering_args(request, used_base_type)
# def read_all(
#         serialization_modifiers: RequestArgsParser.Result,
#         filtering_query_mod: Callable[[Query], Query], **kwargs
# ):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
#             serialization_modifiers,
#             filtering_query_mod
#             )()
#
#
# @countries.get('/<id>')
# @serialization_args(request, used_base_type)
# def get_country(
#         name: str, serialization_modifiers: RequestArgsParser.Result, requestor_employee: Employee
# ):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(
#         serialization_modifiers)()
#
#
# @countries.put('/<id>')
# @login_required
# @permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
# def update_country(name: str, requestor_employee: Employee):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).get_crud_update_body()()
#
#
# @countries.delete('/<id>')
# @login_required
# @permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
# def delete(name: str, requestor_employee: Employee):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).get_crud_delete_body()()


registered = (BlueprintDefaults('countries', Country, DefaultExtraValidators)
              .default()
              .permissions_Set(RequiredPermissionsFlag.HEAD_MANAGER)
              .useDefault_CreateRequest()
              .useDefault_DeleteRequest()
              .useDefault_UpdateRequest()
              .permissions_Clear()
              .modifiers_Remove(RequestModifiers.LOGIN)
              .useDefault_ReadManyRequest()
              .useDefault_ReadSingleRequest()
              )
