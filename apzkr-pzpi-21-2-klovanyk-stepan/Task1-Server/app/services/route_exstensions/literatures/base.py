from abc import ABC, abstractmethod
from http import HTTPStatus
from os import PathLike
from typing import cast, Callable, AnyStr, BinaryIO

from flask import Request, Response, request, send_file
from icecream import ic
from sqlalchemy import Delete
from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage

from app.database.models import Literature, Base
from app.services.creators.builders.routes import RoutesBuilder
from app.services.creators.factories.body_details import BodyFactoryDetailsFactory, BodyFactoryDetails
from app.services.processors.tools import RequestHelper
from app.services.validators.base import ValidationException, ValidationExceptionType
from app.services.validators.crud import ReadOrDeleteValidationResult
from app.utils.extra import GeneralResponse
from app.utils.file_manager.files import FileManager


class LiteratureFileManagingBase[T: ReadOrDeleteValidationResult, R: None](
    RoutesBuilder.AdvancedDetailsBase[T, R], ABC
):
    @abstractmethod
    def on_successful_literature_fetch(
            self,
            literature: Literature,
            session: Session,
            request_args: dict[str, any],
    ) -> R:
        raise NotImplementedError()

    def before_result_callback(self, result: T, session: Session, request_args: dict[str, any]) -> R:
        literature = cast(Literature, result.object)
        # self.unique_root_ident = literature.id
        request_args['literature'] = literature
        return self.on_successful_literature_fetch(
            literature,
            session,
            request_args
        )

    def details_provider(self, body_factory_details_factory: BodyFactoryDetailsFactory) \
            -> Callable[[Callable[[T, dict[str, any]], R]], BodyFactoryDetails]:
        return body_factory_details_factory.READ_ONE

    def __init__(self):
        super().__init__()
        self.file_manager = FileManager()
        self.registered_root = FileManager.RegisteredRoots.Literatures

    @abstractmethod
    def get_file_name(self, literature: Literature) -> str:
        return NotImplemented()


class LiteratureFilesPostingBase[T: ReadOrDeleteValidationResult, R: None](
    LiteratureFileManagingBase[T, R], ABC
):
    @staticmethod
    def _get_file_from_request(request_: Request) -> FileStorage:
        if request_.content_type.find('multipart/form-data') == -1:
            raise ValidationException(
                ValidationExceptionType.INVALID_CONTENT_TYPE,
                HTTPStatus.BAD_REQUEST,
                "Use multipart/form-data"
            )
        if not (file := request_.files.get('file')):
            raise ValidationException(
                ValidationExceptionType.REQUEST_MISSING_FILE, HTTPStatus.BAD_REQUEST, "Use 'file' as a key for the file"
            )
        return file

    def response_mod(self, response: T, session: Session, request_data: dict[str, any]) -> dict | Response:
        return GeneralResponse.FILE_ADDED.embed(f"{Literature.__name__}[id={request_data['literature'].id}]")

    def on_successful_literature_fetch(
            self,
            literature: Literature,
            session: Session,
            request_args: dict[str, any]
    ) -> R:
        file = self._get_file_from_request(request)
        unique_root_ident = literature.id
        self.file_manager.loyal_delete(
            self.get_file_name(literature), self.registered_root, str(unique_root_ident)
        )
        self.file_manager.save(
            file, self.registered_root, str(unique_root_ident),
            allowed_file_types=self.get_allowed_file_types()
        )
        RequestHelper.update_to_db(session, literature, {self.get_literature_saving_key(Literature): file.filename})

    @abstractmethod
    def get_literature_saving_key(self, base: type[Literature]) -> str:
        return NotImplemented()

    def methods_provider(self) -> list[str]:
        return ['POST']

    @abstractmethod
    def get_allowed_file_types(self) -> list[FileManager.FileType]:
        return NotImplemented()


class LiteratureThumbnailFileName[T: ReadOrDeleteValidationResult, R: None](
    LiteratureFileManagingBase[T, R], ABC
):
    def get_file_name(self, literature: Literature) -> str:
        return literature.thumbnail_PATH


class LiteraturePdfFileName[T: ReadOrDeleteValidationResult, R: None](
    LiteratureFileManagingBase[T, R], ABC
):
    def get_file_name(self, literature: Literature) -> str:
        return literature.pdf_PATH


class LiteratureFilesGettingBase[T: ReadOrDeleteValidationResult, R: None](
    LiteratureFileManagingBase[T, R], ABC
):
    def response_mod(self, response: T, session: Session, request_args: dict[str, any]) -> dict | Response:
        final_path = self.file_manager.full_path(
            self.get_file_name(request_args['literature']),
            self.registered_root,
            str(request_args['literature'].id)
        )
        return send_file(
            self.get_file(final_path),
            mimetype=self.get_mimetype(),
            download_name=self.get_download_name(request_args['literature'])
        )

    @abstractmethod
    def get_file(self, path: str) -> str | PathLike[AnyStr] | BinaryIO:
        return NotImplemented()

    def __init__(self):
        super().__init__()
        # self.mimetype: str | None = None
        # self.result_file_name: str | None = None
        # self.download_name: str | None = None

    def on_successful_literature_fetch(
            self,
            literature: Literature,
            session: Session,
            request_args: dict[str, any]
    ) -> R:
        if not (file_name := self.get_file_name(literature)):
            raise ValidationException(ValidationExceptionType.RESOURCE_NOT_FOUND, HTTPStatus.NOT_FOUND)
        # ic(file_name, literature.thumbnail_PATH)
        request_args['literature'] = literature
        return

    def methods_provider(self) -> list[str]:
        return ["GET"]

    @abstractmethod
    def get_mimetype(self) -> str:
        return NotImplemented()

    @abstractmethod
    def get_download_name(self, literature: Literature) -> str:
        return NotImplemented()


class DropDetailsBase[T: ReadOrDeleteValidationResult, R: None](
    RoutesBuilder.AdvancedDetailsBase[T, R], ABC
):
    def details_provider(self, body_factory_details_factory: BodyFactoryDetailsFactory) \
            -> Callable[[Callable[[T, dict[str, any]], R]], BodyFactoryDetails]:
        return body_factory_details_factory.READ_ONE

    def methods_provider(self) -> list[str]:
        return ["DELETE"]

    def response_mod(self, response: any, session: Session, request_data: dict[str, any]) -> dict:
        return {"message": self.response_message()}

    @abstractmethod
    def response_message(self) -> str:
        return NotImplemented()

    def before_result_callback(self, result: T, session: Session, request_args: dict[str, any]) -> R:
        session.execute(
            self.delete_statement(result.object)
        )
        session.commit()
        return

    @abstractmethod
    def delete_statement(self, object: Base) -> Delete:
        return NotImplemented()
