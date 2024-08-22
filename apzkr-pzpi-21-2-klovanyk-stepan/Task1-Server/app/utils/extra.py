import enum
from abc import abstractmethod, ABC
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, asdict
from http import HTTPStatus
from pathlib import Path
from typing import Callable

from flask import Blueprint
from sqlalchemy import Column
from sqlalchemy.orm import RelationshipProperty, InstrumentedAttribute, Session

from app.database.models import Base, User
from app.database.schemas import BaseSchema
from app.utils.base import SingletonMeta, SingletonAbstractMeta
from app.services.validators.base import ValidationException


class SecondaryConfig(metaclass=SingletonMeta):
    def __init__(self):
        self.BLUEPRINTS_PATH = Path('app', 'blueprints')
        self.ESTABLISHMENT_PORT_RANGE = (49152, 65535)
        self.IOT_REG_FILE_NAME = 'IOT_REG'

    class FlaskAppConfig:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10, 'pool_recycle': 3600, 'pool_pre_ping': True
        }


class BlueprintsStorage(metaclass=SingletonMeta):
    def __init__(self):
        self.blueprints: set[Blueprint] = set()

    def register(self, blueprint: Blueprint):
        self.blueprints.add(blueprint)


@dataclass
class ValidatorsData[DbObject: Base, DbUser: User]:
    validate_DataWithUser: Callable[[DbUser, DbObject, dict[str, any] | None, Session], ValidationException | None] \
        = lambda *_: None
    validate_User: Callable[[DbUser, Session], ValidationException | None] = lambda *_: None
    validate_NoUser: Callable[[], ValidationException | None] = lambda: None
    validate_DataWithoutUser: Callable[[DbObject, dict[str, any] | None, Session], ValidationException | None] = \
        lambda *_: \
            None

    def set_DataWithUserValidator(
            self,
            func: Callable[[DbUser, DbObject, dict[str, any] | None, Session], ValidationException | None]
    ):
        self.validate_DataWithUser = func
        return self

    def set_UserValidator(self, func: Callable[[DbUser, Session], ValidationException | None]):
        self.validate_User = func
        return self

    def set_NoUserValidator(self, func: Callable[[], ValidationException | None]):
        self.validate_NoUser = func
        return self

    def set_DataWithoutUserValidator(
            self,
            func: Callable[[DbObject, dict[str, any] | None, Session], ValidationException | None]
    ):
        self.validate_DataWithoutUser = func
        return self

    def extend_DataWithUserValidator(
            self,
            func: Callable[[DbUser, DbObject, dict[str, any] | None, Session], ValidationException | None],
            inject_as_first: bool = False
    ):
        first, second = (self.validate_DataWithUser, func) if not inject_as_first else (
            func, self.validate_DataWithUser)
        self.validate_DataWithUser = merge_handlers(first, second)
        return self

    def extend_UserValidator(
            self,
            func: Callable[[DbUser, Session], ValidationException | None],
            inject_as_first: bool = False
    ):
        first, second = (self.validate_User, func) if not inject_as_first else (func, self.validate_User)
        self.validate_User = merge_handlers(first, second)
        return self

    def extend_NoUserValidator(
            self,
            func: Callable[[], ValidationException | None],
            inject_as_first: bool = False
    ):
        first, second = (self.validate_NoUser, func) if not inject_as_first else (func, self.validate_NoUser)
        self.validate_NoUser = merge_handlers(first, second)
        return self

    def extend_DataWithoutUserValidator(
            self,
            func: Callable[[DbObject, dict[str, any] | None, Session], ValidationException | None],
            inject_as_first: bool = False
    ):
        first, second = (self.validate_DataWithoutUser, func) if not inject_as_first else (
            func, self.validate_DataWithoutUser)
        self.validate_DataWithoutUser = merge_handlers(first, second)
        return self


class ExtraValidatorsStorageBase(ABC):
    @abstractmethod
    def _init_validators(self) -> dict[type[Base], ValidatorsData]:
        raise NotImplementedError()

    def __init__(self):
        self._validators = self._init_validators()

    def __getitem__[T: Base](self, base_type: type[T]) -> ValidatorsData[T, User]:
        return self._validators[base_type]


class _ExtraValidatorsStorageBaseSingleton(
    ExtraValidatorsStorageBase, ABC, metaclass=SingletonAbstractMeta
):
    def snapshot(self) -> type[ExtraValidatorsStorageBase]:
        snapshot_validators = deepcopy(self._validators)

        class SnapshotExtraValidators(ExtraValidatorsStorageBase):
            def _init_validators(self) -> dict[type[Base], ValidatorsData]:
                return snapshot_validators

        return SnapshotExtraValidators


class DefaultExtraValidators(_ExtraValidatorsStorageBaseSingleton):
    def _init_validators(self) -> dict[type[Base], ValidatorsData]:
        return {obj: ValidatorsData[obj, User]() for obj in AlchemyExtras().get_all_tables().values()}


class AlchemyExtras(metaclass=SingletonMeta):
    def __init__(self):
        self._TABLE_NAMES_MAPPING_: dict[str, type[Base]] = {}
        self._TABLES_SCHEMA_MAPPING_: dict[type[Base], type[BaseSchema]] = {schema.Meta.model: schema for schema in
                                                                            BaseSchema.__subclasses__()}
        self._COLUMNS_PER_TABLE_: dict[type[Base], dict[str, Column]] = defaultdict(dict)
        self._PK_PER_TABLE_: dict[type[Base], set[Column]] = {}

        self._RELATIONS_PER_TABLE_: dict[type[Base], set[RelationshipProperty]] = defaultdict(set)
        self._PARENT_AND_CHILD_PER_RELATION_: dict[RelationshipProperty, list[tuple[Column, Column]]] = defaultdict(
            lambda: list()
        )
        self._PARENT_AND_CHILDREN_PER_COLUMN_: dict[Column, list] = defaultdict(
            lambda: [None, set()]
        )

        for value in Base.registry._class_registry.values():
            if isinstance(value, type(Base)) and hasattr(value, '__tablename__'):
                table_base: type[Base] = value
                table_name: str = table_base.__tablename__
                self._TABLE_NAMES_MAPPING_[table_name] = table_base
                self._COLUMNS_PER_TABLE_[table_base] = {col.name: col for col in table_base.__mapper__.columns}
                self._PK_PER_TABLE_[table_base] = {col for col in table_base.__mapper__.columns if col.primary_key}

        for value in Base.registry._class_registry.values():
            if isinstance(value, type(Base)) and hasattr(value, '__tablename__'):
                table_base: type[Base] = value
                relationships: list[RelationshipProperty] = [i for i in table_base.__mapper__.relationships]
                for relationship in relationships:
                    self._RELATIONS_PER_TABLE_[table_base].add(relationship)
                    children_of_relationship: list[Column] = list(relationship._calculated_foreign_keys)
                    for child_of_relationship in children_of_relationship:
                        parents_of_child = child_of_relationship.foreign_keys
                        assert len(parents_of_child) == 1
                        parent_table_name, parent_column_name = list(parents_of_child)[0].target_fullname.split('.')
                        parent_of_child = self._COLUMNS_PER_TABLE_[self.get_table_by_name(parent_table_name)][
                            parent_column_name]
                        self._PARENT_AND_CHILD_PER_RELATION_[relationship].append(
                            (parent_of_child, child_of_relationship)
                        )
                        self._PARENT_AND_CHILDREN_PER_COLUMN_[parent_of_child][1].add(child_of_relationship)
                        self._PARENT_AND_CHILDREN_PER_COLUMN_[child_of_relationship][0] = parent_of_child

    def get_schema_of(self, table: type[Base]) -> type[BaseSchema]:
        return self._TABLES_SCHEMA_MAPPING_[table]

    def get_relationships_of(self, table: type[Base]) -> set[RelationshipProperty]:
        return self._RELATIONS_PER_TABLE_[table]

    def get_column_of(self, table: type[Base], instrumented_attribute: InstrumentedAttribute) -> Column:
        return self.get_columns_of(table)[instrumented_attribute.key]

    def get_all_tables(self) -> dict[str, type[Base]]:
        return self._TABLE_NAMES_MAPPING_

    def get_table_by_name(self, table_name: str) -> type[Base]:
        return self._TABLE_NAMES_MAPPING_[table_name]

    def get_columns_of(self, table: type[Base]) -> dict[str, Column]:
        return self._COLUMNS_PER_TABLE_[table]

    def get_pk_of(self, table: type[Base]) -> set[Column]:
        return self._PK_PER_TABLE_[table]

    def get_relationship_parent_and_child_pairs(self, relationship: RelationshipProperty) -> list[
        tuple[Column, Column]]:
        return self._PARENT_AND_CHILD_PER_RELATION_[relationship]

    def get_parent_and_children_of(self, column: Column) -> tuple[Column, set[Column]]:
        parent, children = self._PARENT_AND_CHILDREN_PER_COLUMN_[column]
        return parent, children

    def get_where_clause(self, obj: Base):
        primary_keys = self.get_pk_of(obj.__class__)
        return {column == getattr(obj, column.key) for column in primary_keys}


class GeneralResponse(enum.Enum):
    FILE_ADDED = ('File was successfully added to {}', HTTPStatus.OK)
    CREATED = ('{} created', HTTPStatus.CREATED)
    UPDATED = ('{} updated', HTTPStatus.OK)
    DELETED = ('{} deleted', HTTPStatus.OK)

    def embed(self, data):
        return self.value[0].format(data), self.value[1]


class CRUDResponse(enum.Enum):
    @dataclass
    class Data:
        success_message: str
        pk_data: dict[str, any] | None

        def with_pk_data(self, pk_data: dict[str, any]):
            return self.__class__(self.success_message, pk_data)

        def with_message_context(self, message_context: str):
            return self.__class__(self.success_message.format(message_context), self.pk_data)

    CREATED = (Data('{} created', None), HTTPStatus.CREATED)
    UPDATED = (Data('{} updated', None), HTTPStatus.OK)
    DELETED = (Data('{} deleted', None), HTTPStatus.OK)

    def embed_pk_data(self, pk_data: dict[str, any], message_context: str):
        return asdict(self.value[0].with_pk_data(pk_data=pk_data).with_message_context(message_context)), self.value[1]

    def embed_pk_data_from_object(self, obj: Base, message_context: str):
        pk_info = AlchemyExtras().get_pk_of(obj.__class__)
        return self.embed_pk_data({col.key: getattr(obj, col.key) for col in pk_info}, message_context)


def merge_callbacks[** P](*callables: Callable[P, None]) -> Callable[P, None]:
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        for func in callables:
            if func:
                func(*args, **kwargs)

    return wrapper


def merge_handlers[T: (ValidationException, None), ** P](*handlers: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        for handler in handlers:
            if handler and (exception := handler(*args, **kwargs)):
                return exception

    return wrapper


def merge_chained[T: any, ** P](*chained_callables: Callable[[T, P], T] | Callable[[T], T]) \
        -> Callable[[T, P], T] | Callable[[T], T]:
    def wrapper(chained: T, *args: P.args, **kwargs: P.kwargs):
        result = chained
        for func in chained_callables:
            if func:
                result = func(result, *args, **kwargs)
        return result

    return wrapper


def combined_injected_validation[T: Base](
        validation_data: ValidatorsData[T, User],
        bound_user: User,
        obj: T,
        session: Session,
        new_object_data: dict[str, any] | None = None
):
    if validation_result := validation_data.validate_User(bound_user, session):
        raise validation_result
    if validation_result := validation_data.validate_DataWithUser(
            bound_user,
            obj,
            new_object_data,
            session
    ):
        raise validation_result
