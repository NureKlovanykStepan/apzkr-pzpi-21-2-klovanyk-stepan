import shutil
from enum import StrEnum
from http import HTTPStatus
from pathlib import Path

from werkzeug.datastructures import FileStorage

from app import SingletonMeta
from app.services.validators.base import ValidationException, ValidationExceptionType


class FileManager(metaclass=SingletonMeta):
    class RegisteredRoots(StrEnum):
        Literatures = "Literatures"

    class FileType(StrEnum):
        PDF = "pdf"
        IMAGE = "image"

    def __init__(self, root_path: Path = None):
        self.main_root_path = root_path
        if not self.main_root_path.exists():
            self.main_root_path.mkdir()

    def save(
            self, file: FileStorage, registered_root: RegisteredRoots, /, unique_root_path: str = "",
            file_name: str = None, allowed_file_types: list[FileType] | None = None
    ):
        if allowed_file_types is not None:
            if not any(file.content_type.find(t) != -1 for t in allowed_file_types):
                raise ValidationException(ValidationExceptionType.INVALID_CONTENT_TYPE, HTTPStatus.BAD_REQUEST, file)

        final_root_path = self.main_root_path / registered_root / str(unique_root_path)
        if not final_root_path.exists():
            final_root_path.mkdir(parents=True)
        if not file_name:
            file_name = file.filename
        file.save((final_path := final_root_path / file_name))
        return final_path

    def loyal_delete(self, file_name: str | None, registered_root: RegisteredRoots, /, unique_root_path: str = ""):
        if not file_name:
            return
        try:
            (self.main_root_path / registered_root / str(unique_root_path) / file_name).unlink()
        except FileNotFoundError:
            pass

    def delete_path(self, path: Path):
        path.unlink()

    def full_path(self, file_name: str, registered_root: RegisteredRoots, /, unique_root_path: str = ""):
        return self.main_root_path / registered_root / str(unique_root_path) / file_name

    def destroy_root(self, registered_root: RegisteredRoots, /, unique_root_path: str = ""):
        if (root_path := self.main_root_path / registered_root / str(unique_root_path)).exists():
            shutil.rmtree(root_path)
