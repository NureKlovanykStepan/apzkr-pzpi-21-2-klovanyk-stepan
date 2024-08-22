from http import HTTPStatus
from io import BytesIO
from os import PathLike
from typing import AnyStr, BinaryIO, cast, Callable

from PIL import Image
from flask import Response, request
from flask_login import current_user
from icecream import ic
from sqlalchemy import Delete, delete
from sqlalchemy.orm import Session, Query

from app.database.models import Literature, Base, LiteratureGenre, LiteratureAuthor, Author
from app.services.creators.builders.routes import RoutesBuilder
from app.services.creators.factories.body_details import BodyFactoryDetailsFactory, BodyFactoryDetails
from app.services.processors.tools import RequestHelper
from app.services.route_exstensions.literatures.base import LiteratureFileManagingBase, LiteratureFilesPostingBase, \
    LiteratureThumbnailFileName, LiteraturePdfFileName, LiteratureFilesGettingBase, DropDetailsBase
from app.services.route_exstensions.literatures.validators_additions import is_user_can_fully_read_any_literature, \
    availableLiteratures_ForEmployeeToRead, availableLiteratures_ForEmployeeToEdit, availableLiteratures_ForUser, \
    multi_genre_filtering_query_mod
from app.services.validators.base import ValidationException, ValidationExceptionType
from app.services.validators.crud import ReadOrDeleteValidationResult
from app.utils.file_manager.files import FileManager


class LiteratureRootDestroyingDetailsImpl[T: ReadOrDeleteValidationResult, R: None](
    LiteratureFileManagingBase[T, R]
):

    def on_successful_literature_fetch(
            self,
            literature: Literature,
            session: Session,
            request_args: dict[str, any]
    ) -> R:
        unique_root_ident = literature.id
        self.file_manager.destroy_root(
            self.registered_root, str(unique_root_ident)
        )

    def get_file_name(self, literature: Literature) -> str:
        return ""

    def response_mod(self, response: any, session: Session, request_data: dict[str, any]) -> dict | Response:
        return response

    def methods_provider(self) -> list[str]:
        return ["DELETE"]


class LiteratureThumbnailPostingImpl[T: ReadOrDeleteValidationResult, R: None](
    LiteratureFilesPostingBase[T, R],
    LiteratureThumbnailFileName[T, R],
):
    def get_literature_saving_key(self, base: type[Literature]) -> str:
        return Literature.thumbnail_PATH.key

    def get_allowed_file_types(self):
        return [FileManager.FileType.IMAGE]


class LiteraturePdfPostingImpl[T: ReadOrDeleteValidationResult, R: None](
    LiteratureFilesPostingBase[T, R],
    LiteraturePdfFileName[T, R],
):
    def get_literature_saving_key(self, base: type[Literature]) -> str:
        return Literature.pdf_PATH.key

    def get_allowed_file_types(self):
        return [FileManager.FileType.PDF]


class LiteratureThumbnailGettingImpl[T: ReadOrDeleteValidationResult, R: None](
    LiteratureFilesGettingBase[T, R],
    LiteratureThumbnailFileName[T, R]
):
    def get_file(self, path: str) -> str | PathLike[AnyStr] | BinaryIO:
        try:
            # ic(path)
            image = Image.open(path)
        except Exception as any_e:
            # ic(any_e)
            raise ValidationException(
                ValidationExceptionType.RESOURCE_NOT_FOUND, HTTPStatus.NOT_FOUND, any_e
            )

        width, height, quality = request.args.get("width"), request.args.get("height"), request.args.get("quality")
        width, height, quality = width and int(width), height and int(height), quality and float(quality)
        if not (width or height or quality):
            return path
        if (width or height) and quality:
            raise ValidationException(
                ValidationExceptionType.RELATIVE_AND_ABSOLUTE_CONFLICT, HTTPStatus.BAD_REQUEST
            )
        if quality and not 0 < quality <= 1:
            raise ValidationException(
                ValidationExceptionType.INVALID_QUALITY,
                HTTPStatus.BAD_REQUEST,
                "Must be between 0 exclusive and 1 inclusive"
            )
        if quality:
            width, height = int(image.width * quality), int(image.height * quality)
        elif width and not height:
            height = int(image.height * width / image.width)
        elif height and not width:
            width = int(image.width * height / image.height)

        image = image.convert('RGB')
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        bytes = BytesIO()
        image.save(bytes, format="JPEG")
        bytes.seek(0)
        return bytes

    def get_mimetype(self) -> str:
        return "image/jpeg"

    def get_download_name(self, literature: Literature) -> str:
        return f"{literature.name}_thumbnail.jpg"


class LiteraturePdfGettingImpl[T: ReadOrDeleteValidationResult, R: None](
    LiteratureFilesGettingBase[T, R],
    LiteraturePdfFileName[T, R]
):
    def get_file(self, path: str) -> str | PathLike[AnyStr] | BinaryIO:
        return path

    def get_mimetype(self) -> str:
        return "application/pdf"

    def get_download_name(self, literature: Literature) -> str:
        return f"{literature.name}.pdf"


class LiteratureDropGenresDetailsImpl[T: ReadOrDeleteValidationResult, R: None](DropDetailsBase[T, R]):

    def delete_statement(self, object: Base) -> Delete:
        return delete(LiteratureGenre).where(LiteratureGenre.literature_id == cast(Literature, object).id)

    def response_message(self):
        return "Literature genres deleted"


class LiteratureDropAuthorsDetailsImpl[T: ReadOrDeleteValidationResult, R: None](DropDetailsBase[T, R]):

    def delete_statement(self, object: Base) -> Delete:
        return delete(LiteratureAuthor).where(LiteratureAuthor.literature_id == cast(Author, object).id)

    def response_message(self):
        return "Literature authors deleted"


class LiteratureFullyReadableDetailsImpl[T: Query, R: Query](
    RoutesBuilder.AdvancedDetailsBase[T, R]
):
    def response_mod(self, response: any, session: Session, request_data: dict[str, any]) -> dict:
        return response

    def before_result_callback(self, result: T, session: Session, request_args: dict[str, any]) -> R:
        def inside():
            bound_user = RequestHelper.get_current_bound_user(session, current_user)
            if not is_user_can_fully_read_any_literature(bound_user, session):
                raise ValidationException(
                    ValidationExceptionType.NOT_ENOUGH_PERMISSIONS,
                    HTTPStatus.FORBIDDEN
                )

            if employee := bound_user.employee:
                if employee.establishment.company.global_access_company:
                    return result
                return availableLiteratures_ForEmployeeToRead(result, employee)

            return availableLiteratures_ForUser(result, bound_user, session)

        return multi_genre_filtering_query_mod(inside(), request_args)

    def details_provider(self, body_factory_details_factory: BodyFactoryDetailsFactory) \
            -> Callable[[Callable[[T, dict[str, any]], R]], BodyFactoryDetails]:
        return body_factory_details_factory.READ_MANY

    def methods_provider(self) -> list[str]:
        return ["GET"]


class LiteratureFullyEditableDetailsImpl[T: Query, R: Query](
    RoutesBuilder.AdvancedDetailsBase[T, R]
):
    def response_mod(self, response: any, session: Session, request_data: dict[str, any]) -> dict:
        return response

    def before_result_callback(self, result: T, session: Session, request_args: dict[str, any]) -> R:
        def inside():
            bound_user = RequestHelper.get_current_bound_user(session, current_user)
            if not (employee := bound_user.employee):
                raise ValidationException(
                    ValidationExceptionType.NOT_EMPLOYEE,
                    HTTPStatus.FORBIDDEN
                )
            if employee.establishment.company.global_access_company:
                return result
            return availableLiteratures_ForEmployeeToEdit(result, employee)

        return multi_genre_filtering_query_mod(inside(), request_args)

    def details_provider(self, body_factory_details_factory: BodyFactoryDetailsFactory) \
            -> Callable[[Callable[[T, dict[str, any]], R]], BodyFactoryDetails]:
        return body_factory_details_factory.READ_MANY

    def methods_provider(self) -> list[str]:
        return ["GET"]
