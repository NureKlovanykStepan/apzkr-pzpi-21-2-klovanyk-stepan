from __future__ import annotations

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Callable, cast

import sqlalchemy.engine.row
from icecream import ic
from sqlalchemy import Column
from sqlalchemy.orm import Session, object_session

from app.database.models import Base, User, Country
from app.utils.extra import AlchemyExtras, ExtraValidatorsStorageBase


class FilteringOptions[T]:
    def __init__(self, predicate: Callable[[T], bool]):
        self.predicate: Callable[[T], bool] = predicate

    def list(self, items: list[T]) -> list[T]:
        return [item for item in items if self.predicate(item)]

    def dict_keys(self, items: dict[T, any]) -> dict[T, any]:
        return {key: value for key, value in items.items() if self.predicate(key)}

    def dict_values(self, items: dict[any, T]) -> dict[any, T]:
        return {key: value for key, value in items.items() if self.predicate(value)}


class DataFilter[T](ABC):
    def __init__(self):
        self._options = FilteringOptions[T](self.predicate)

    @abstractmethod
    def predicate(self, item: T) -> bool:
        raise NotImplementedError()

    @property
    def filter_on(self) -> FilteringOptions[T]:
        return self._options


class ColumnFilterBase(DataFilter[Column], ABC):
    def __init__(self, is_exclude_mode: bool):
        super().__init__()
        self.columns: set[Column] = set()
        self.is_exclude_mode: bool = is_exclude_mode

    def predicate(self, item: Column) -> bool:
        return self._is_item_excluded(item) if self.is_exclude_mode else self._is_item_included(item)

    @abstractmethod
    def _is_item_included(self, item: Column) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def _is_item_excluded(self, item: Column) -> bool:
        raise NotImplementedError()


class DummyColumnFilter(ColumnFilterBase):

    def _is_item_included(self, item: Column) -> bool:
        return True

    def _is_item_excluded(self, item: Column) -> bool:
        return True


class ExplicitColumnFilter(ColumnFilterBase):

    def _is_item_included(self, item: Column) -> bool:
        return item in self.columns

    def _is_item_excluded(self, item: Column) -> bool:
        return item not in self.columns


class CombinedColumnFilter(DataFilter[Column]):
    def predicate(self, item: Column) -> bool:
        return self.included.predicate(item) and self.excluded.predicate(item)

    def __init__(self, included: ColumnFilterBase, excluded: ColumnFilterBase):
        super().__init__()
        self.included = included
        self.excluded = excluded


class CombinedColumnFilterBuilder:
    def __init__(self):
        self.included: ColumnFilterBase = ExplicitColumnFilter(False)
        self.excluded: ColumnFilterBase = ExplicitColumnFilter(True)

    def include_columns(self, *columns: Column):
        for column in columns:
            self.included.columns.add(column)
        return self

    def exclude_columns(self, *columns: Column):
        for column in columns:
            self.excluded.columns.add(column)
        return self

    def include_tables(self, *tables: type[Base]):
        for table in tables:
            for column in AlchemyExtras().get_columns_of(table).values():
                self.included.columns.add(column)
        return self

    def exclude_tables(self, *tables: type[Base]):
        for table in tables:
            for column in AlchemyExtras().get_columns_of(table).values():
                self.excluded.columns.add(column)
        return self

    def build(self):
        return CombinedColumnFilter(self.included, self.excluded)


class SerializationThreadingMode(IntEnum):
    DISABLED = auto()
    FULL = auto()
    PARTIAL = auto()


@dataclass
class SerializerOptions:
    threading_mode: SerializationThreadingMode = SerializationThreadingMode.PARTIAL
    threading_partial_threshold: int = 2000


class ObjectSerializationResultAssembler:

    @classmethod
    def empty(cls):
        return cls.Result()

    def __init__(
            self, obj: Base,
            recursive_layer_handler_builder: Callable[
                [Base | list[Base], list[tuple[Column, Column]]], LayerProcessorBase]
    ):
        self.obj = obj
        self.recursive_layer_handler_builder = recursive_layer_handler_builder
        self._result = self.empty()
        self._cols_to_serialize = AlchemyExtras().get_columns_of(obj.__class__)
        self._relationships_to_serialize = {
            relationship: AlchemyExtras().get_relationship_parent_and_child_pairs(relationship) for relationship in
            AlchemyExtras().get_relationships_of(obj.__class__)
        }
        self._later_excluded_pairs: list[tuple[Column, Column]] = []

    @dataclass
    class Result:
        dict_data: dict[str, any] = field(default_factory=dict)
        sync_calls: list[Callable[[], None]] = field(default_factory=list)

    def apply_columns_filter(self, filter_: Callable[[dict[str, Column]], dict[str, Column]]):
        self._cols_to_serialize = filter_(self._cols_to_serialize)
        return self

    def apply_relationships_filter(self, excluded_pairs: list[tuple[Column, Column]]):
        self._later_excluded_pairs += excluded_pairs
        self._relationships_to_serialize = {
            rel: [tuple([parent, child])
                  for parent, child in pairs if
                  [self._ident(parent), self._ident(child)] not in [[self._ident(e_parent), self._ident(e_child)] for
                                                                    e_parent,
                                                                    e_child in
                                                                    excluded_pairs]]
            for rel, pairs in self._relationships_to_serialize.items()
        }
        return self

    def _ident(self, col: Column):
        return f'{col.table.name}.{col.key}'

    def build_result(self):
        self._result_builder()
        return self._result

    def _result_builder(self):
        if not self._cols_to_serialize:
            return
        self._apply_columns_data()
        self._apply_relations_data()

    def _apply_columns_data(self):
        for column in self._cols_to_serialize.values():
            self._result.dict_data[column.key] = getattr(self.obj, column.key)

    def _create_sync_call(self, key: str, pairs_to_exclude: list[tuple[Column, Column]]):
        adjusted_excluded_pairs = self._later_excluded_pairs + [*pairs_to_exclude, *[pair[::-1]
                                                                                     for pair in pairs_to_exclude]]
        fill_on_key = key

        def call():
            data = getattr(self.obj, fill_on_key)
            next_layer_handler = self.recursive_layer_handler_builder(data, adjusted_excluded_pairs)
            inner_data = next_layer_handler.handle_data()
            if type(inner_data) is dict and not inner_data:
                return
            self._result.dict_data[fill_on_key] = inner_data

        return call

    def _apply_relations_data(
            self,
    ):
        for relationship, pairs in self._relationships_to_serialize.items():
            for parent, child in pairs:
                if parent.key in self._cols_to_serialize or child.key in self._cols_to_serialize:
                    self._result.sync_calls.append(self._create_sync_call(relationship.key, pairs))


class LayerProcessorBase(ABC):
    def __init__(
            self,
            object_one_or_many: Base | list[Base],
            excluded_relation_pairs: list[tuple[Column, Column]],
            columns_filter: Callable[[dict[str, Column]], dict[str, Column]],
            next_layer_handler_retriever: Callable[[], type[LayerProcessorBase]],
            requestor: User | None,
            extra_validation_data_storage: type[ExtraValidatorsStorageBase],
            session: Session,
            result_builder: type[ObjectSerializationResultAssembler] = ObjectSerializationResultAssembler,
    ):
        self.object_one_or_many = object_one_or_many
        self.excluded_relation_pairs = excluded_relation_pairs
        self.columns_filter = columns_filter
        self.requestor = requestor
        self.next_layer_handler_retriever = next_layer_handler_retriever
        self.extra_validation_data_storage = extra_validation_data_storage
        self.session = session
        self.result_builder = result_builder

    def handle_data(self):
        if isinstance(many := self.object_one_or_many, list):
            if self._is_empty() or not self._is_level_access_allowed(many[0]):
                return []
            return self._handle_many(self._filter_many_with_validation(many))
        elif isinstance(single := self.object_one_or_many, Base):
            if not self._is_level_access_allowed(single) or not self._is_item_allowed(single):
                return {}
            return self._handle_single(single)

    @abstractmethod
    def _handle_many(self, objs: list[Base]) -> list[dict[str, any]]:
        pass

    def _filter_many_with_validation(self, objs: list[Base]) -> list[Base]:
        return [obj for obj in objs if self._is_item_allowed(obj)]

    def _handle_single(self, obj: Base) -> dict[str, any]:
        return self._result_sync_only_finalizer(self._serialize(obj))

    @staticmethod
    def _result_sync_only_finalizer(result: ObjectSerializationResultAssembler.Result) -> dict[str, any]:
        [call() for call in result.sync_calls]
        return result.dict_data

    @staticmethod
    def _check_continuum_allowed(result: ObjectSerializationResultAssembler.Result):
        return not not result.dict_data

    def _is_empty(self):
        return isinstance(self.object_one_or_many, list) and not self.object_one_or_many

    def _is_level_access_allowed(self, item: Base):
        if not (storage := self.extra_validation_data_storage):
            return True

        validators_storage = storage()[item.__class__]
        if not self.requestor:
            return not validators_storage.validate_NoUser()
        else:
            return not validators_storage.validate_User(self.requestor, self.session)

    def _is_item_allowed(self, item: Base):
        if not (storage := self.extra_validation_data_storage):
            return True

        validators_storage = storage()[item.__class__]
        if not self.requestor:
            return not validators_storage.validate_DataWithoutUser(item, None, self.session)
        else:
            return not validators_storage.validate_DataWithUser(self.requestor, item, None, self.session)


    def _create_next_layer_handler(
            self,
            object_one_or_many: Base | list[Base],
            adjusted_excluded_pairs: list[tuple[Column, Column]]
    ):
        return self.next_layer_handler_retriever()(
            columns_filter=self.columns_filter,
            excluded_relation_pairs=adjusted_excluded_pairs,
            object_one_or_many=object_one_or_many,
            requestor=self.requestor,
            extra_validation_data_storage=self.extra_validation_data_storage,
            session=self.session,
            result_builder=self.result_builder,
            next_layer_handler_retriever=self.next_layer_handler_retriever
        )

    def _serialize(
            self, obj: Base
    ):
        return (self.result_builder(obj, self._create_next_layer_handler)
                .apply_columns_filter(self.columns_filter)
                .apply_relationships_filter(self.excluded_relation_pairs)
                .build_result()) if not isinstance(obj, sqlalchemy.engine.row.Row) \
            else (self.result_builder.Result(dict(obj._mapping), []))


class SynchronousLayerProcessor(LayerProcessorBase):
    def _handle_many(self, objs: list[Base]) -> list[dict[str, any]]:
        def inner():
            for obj in objs:
                if not self._check_continuum_allowed(raw_result := self._serialize(obj)):
                    break
                if result := self._result_sync_only_finalizer(raw_result):
                    yield result

        return list(inner())


class ThreadedLayerProcessor(LayerProcessorBase):
    def _handle_many(self, objs: list[Base]) -> list[dict[str, any]]:
        def inner():
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures: list[Future] = [executor.submit(self._serialize, obj) for obj in objs if
                                         self._is_item_allowed(obj)]
                for future in as_completed(futures):
                    if not self._check_continuum_allowed(future.result()):
                        [f.cancel() for f in futures if not f.done()]
                        break
                    yield self._result_sync_only_finalizer(future.result())

        return list(inner())


class Serializer2:
    def __init__(
            self,
            initial_object: Base | list[Base],
            requestor: User,
            session: Session,
            modifiers: CombinedColumnFilter = None,
            options: SerializerOptions = None,
            extra_validation_data_storage: type[ExtraValidatorsStorageBase] = None,
    ):
        self.initial_object = initial_object
        self.requestor = requestor
        self.modifiers = modifiers or CombinedColumnFilter(
            included=DummyColumnFilter(False),
            excluded=DummyColumnFilter(True),
        )
        self.options = options or SerializerOptions()
        self.extra_validation_data_storage = extra_validation_data_storage
        self.session = session

    def _use_threading(self):
        if self.options.threading_mode == SerializationThreadingMode.DISABLED:
            return False
        if self.options.threading_mode == SerializationThreadingMode.FULL:
            return True
        if self.options.threading_mode == SerializationThreadingMode.PARTIAL:
            return isinstance(self.initial_object, list) and (len(self.initial_object) >
                                                              self.options.threading_partial_threshold)

    def _layer_handler_retriever(self) -> type[LayerProcessorBase]:
        return ThreadedLayerProcessor if self._use_threading() else SynchronousLayerProcessor

    def serialize(self):
        return (retriever := self._layer_handler_retriever)()(
            object_one_or_many=self.initial_object,
            excluded_relation_pairs=[],
            columns_filter=self.modifiers.filter_on.dict_values,
            # columns_filter=lambda x: x,
            next_layer_handler_retriever=retriever,
            requestor=self.requestor,
            extra_validation_data_storage=self.extra_validation_data_storage,
            session=self.session
        ).handle_data()


class Serializer2Builder:
    def __init__(self):
        self.init_data = {}

    def apply_initial_data(self, initial_object: Base | list[Base]):
        self.init_data.update({'initial_object': initial_object})
        return self

    def apply_modifiers(
            self,
            modifier_actions: Callable[
                [CombinedColumnFilterBuilder], CombinedColumnFilter]
    ):
        self.init_data.update({'modifiers': modifier_actions(CombinedColumnFilterBuilder())})
        return self

    def define_requestor(self, requestor: User):
        self.init_data.update({'requestor': requestor})
        return self

    def apply_options(self, options: SerializerOptions):
        self.init_data.update({'options': options})
        return self

    def apply_extra_validation_data_storage(
            self,
            extra_validation_data_storage: type[ExtraValidatorsStorageBase] | None
    ):
        self.init_data.update({'extra_validation_data_storage': extra_validation_data_storage})
        return self

    def apply_session(self, session: Session):
        self.init_data.update({'session': session})
        return self

    def build(self):
        return Serializer2(**self.init_data)
