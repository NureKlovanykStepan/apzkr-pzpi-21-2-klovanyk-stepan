from app.database.models import Genre
from app.utils.extra import DefaultExtraValidators
from app.services.creators.builders.buieprints import BlueprintDefaults
from app.services.decorators.general.permissions import RequiredPermissionsFlag as Perm


# genres = Blueprint('genres', __name__, url_prefix=SecretConfig().API_PREFIX + '/genres')
# BlueprintsStorage().register(genres)
# used_base_type = Genre


registered_genres = (BlueprintDefaults('genres', Genre, DefaultExtraValidators)
                     .default()
                     .permissions_Set(Perm.LITERATURE_MANAGER)
                     .useDefault_CreateRequest()
                     .useDefault_DeleteRequest()
                     .useDefault_UpdateRequest()
                     .permissions_Clear()
                     .useDefault_ReadSingleRequest()
                     .useDefault_ReadManyRequest()
                     )

# @genres.post('/')
# @login_required
# @permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
# def create_genre(**kwargs):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).getCreationBody()()
#
#
# @genres.get('/')
# @login_required
# @serialization_args(request, used_base_type)
# @filtering_args(request, used_base_type)
# def read_all(
#         serialization_modifiers: RequestArgsParser.Result,
#         filtering_query_mod: Callable[[Query], Query], **kwargs
# ):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).getReadManyBody(
#             serialization_modifiers,
#             filtering_query_mod
#         )()
#
#
#
# @genres.get('/<name>')
# @login_required
# @serialization_args(request, used_base_type)
# def get_genre(
#         name: str, serialization_modifiers: RequestArgsParser.Result, requestor_employee: Employee
# ):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).getReadOneBody(serialization_modifiers)()
#
#
# @genres.put('/<name>')
# @login_required
# @permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
# def update_genre(name: str, requestor_employee: Employee):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).getUpdateBody()()
#
#
# @genres.delete('/<name>')
# @login_required
# @permissions_of_employee_required(current_user, Perm.LITERATURE_MANAGER)
# def delete(name: str, requestor_employee: Employee):
#     with Globals().db.session() as session:
#         return RequestBodyFactory(session, used_base_type, request).getDeleteBody()()
