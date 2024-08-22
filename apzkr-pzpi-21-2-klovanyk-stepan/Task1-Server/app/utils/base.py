from __future__ import annotations

from abc import abstractmethod, ABC, ABCMeta
from enum import StrEnum


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonAbstractMeta(SingletonMeta, ABCMeta):
    pass


class BaseSecretConfig(ABC, metaclass=SingletonAbstractMeta):
    """
    Base configuration class that defines the properties that all configurations must have.
    """

    @abstractmethod
    def get_sqlalchemy_database_uri(self) -> str:
        """
        The URI of the SQLAlchemy database.
        Example: mysql+pymysql://user:password@host:port/database
        """
        raise NotImplementedError()

    @abstractmethod
    def get_secret_key(self) -> str:
        """
        The secret key used for session encryption.
        Any string is valid.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_api_prefix(self) -> str:
        """
        The prefix for all API routes.
        Example: /api/v1
        """
        raise NotImplementedError()

    def get_upload_folder(self) -> str:
        return "FILES"

    @property
    def UPLOAD_FOLDER(self):
        return self.get_upload_folder()

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return self.get_sqlalchemy_database_uri()

    @property
    def SECRET_KEY(self):
        return self.get_secret_key()

    @property
    def API_PREFIX(self):
        return self.get_api_prefix()


class MessageType(StrEnum):
    def as_response(self, http_status_code: int):
        return {"message": self.value}, http_status_code

    def as_response_formatted(self, http_status_code: int, *format_values):
        return {"message": self.value % format_values}, http_status_code
