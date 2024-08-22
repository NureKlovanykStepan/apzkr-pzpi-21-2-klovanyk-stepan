from __future__ import annotations

import re
from collections import UserList, defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Callable, cast

from flask import Request
from icecream import ic
from sqlalchemy import Column
from sqlalchemy.orm import Query

from app.database.models import Base
from app.utils.extra import merge_chained, AlchemyExtras
from app.services.validators.crud import DataTypesAdapter


class RequestQuerySupportedArgs(Enum):
    FILTER = ['filter', 'f', 'fltr', 'filt', 'ftr', 'flt']
    OFFSET = ['offset', 'shift', 'o', 'start', 'from', 'skip', 'of', 'off', 'ofst']
    MAX_COUNT = ['max_count', 'max', 'mc', 'limit', 'count', 'pagesize']
    JOIN = ['join', 'j', 'jn', 'jo', 'jn', 'joi', 'joine', 'joiner']

    @classmethod
    def by_tag(cls, tag: str):
        for enum in cls:
            if tag.lower() in [v.lower() for v in enum.value]:
                return enum
        return None


_args_supported = RequestQuerySupportedArgs


class RequestQueryArgsModifiersStorage:
    _ORDER = [_args_supported.JOIN, _args_supported.FILTER, _args_supported.OFFSET, _args_supported.MAX_COUNT]

    def __init__(self):
        self._modifiers_data: dict[_args_supported, list[Callable[[Query], Query]]] \
            = {e: [] for e in _args_supported}

    def __iter__(self):
        return iter(self[arg] for arg in self._ORDER)

    def __getitem__(self, item: _args_supported):
        storage = self._modifiers_data[item]

        class ModifiersUtils(UserList[Callable[[Query], Query]]):
            def __init__(self):
                super().__init__(storage)
                self.data: list[Callable[[Query], Query]] = storage

            def append_first(self, f: Callable[[Query], Query]):
                self.insert(0, f)

            def merged(self) -> Callable[[Query], Query]:
                return merge_chained(*self.data)

            def merge(self):
                self.data[:] = [self.merged()]

            def __call__(self, data: Query):
                return self.merged()(data)

        return ModifiersUtils()

    def composed(self) -> Callable[[Query], Query]:
        all_merged = [util.merged() for util in self]
        return merge_chained(*all_merged)


class RequestQueryArgsResolver:

    def __init__(self, request: Request, for_type: type[Base]):
        self.all_args = request.args
        self.base_type = for_type
        # ic(request.url)
        self.modifiers_storage = RequestQueryArgsModifiersStorage()
        self._filtered: list[tuple[_args_supported, str]] | None = None

    def process_args(self):
        self._filter_args()
        self._tags_resolve()
        return self.modifiers_storage.composed()

    def _filter_args(self):
        self._filtered = {t: [value for value in values if value]
                          for key in self.all_args
                          if (t := _args_supported.by_tag(key.lower()))
                          and
                          (values := self.all_args.getlist(key))
                          }

    def _tags_resolve(self):
        if self._filtered is None:
            raise ValueError('Args was not filtered')

        for tag, tags_data in self._filtered.items():
            if tag == _args_supported.JOIN:
                self.modifiers_storage[tag].extend(
                    self._resolve_join_tags_data(tags_data)
                )
            elif tag == _args_supported.FILTER:
                self.modifiers_storage[tag].extend(
                    self._resolve_filtering_tags_data(tags_data)
                )
            elif tag == _args_supported.OFFSET:
                self.modifiers_storage[tag].append(
                    self._offset_to_offset_modifier(self._resolve_offset_tags_data(tags_data))
                )
            elif tag == _args_supported.MAX_COUNT:
                self.modifiers_storage[tag].append(
                    self._max_count_to_max_count_modifier(self._resolve_max_count_tags_data(tags_data))
                )

    @classmethod
    def _offset_to_offset_modifier(cls, offset: int) -> Callable[[Query], Query]:
        return lambda query: query.offset(offset)

    @classmethod
    def _max_count_to_max_count_modifier(cls, max_count: int) -> Callable[[Query], Query]:
        return lambda query: cast(Query, query).limit(str(max_count))

    def _resolve_join_tags_data(self, tags_data: list[str]):
        def inner():
            for tag_data in tags_data:
                table = self._table_data_to_table(tag_data)
                yield self._table_to_join_modifier(table)

        return list(inner())

    @classmethod
    def _table_to_join_modifier(cls, table: type[Base]) -> Callable[[Query], Query]:
        def modifier(query: Query):
            return query.join(table)

        return modifier

    def _resolve_filtering_tags_data(self, tags_data: list[str]):
        def inner():
            in_data: dict[type[Base], dict[Column, list[any]]] \
                = defaultdict(lambda: defaultdict(lambda: list()))
            for tag_data in tags_data:
                raw_filtering_data = self._tag_data_to_filtering_data_raw(tag_data)
                filtering_data = self._filtering_data_raw_to_filtering_data(raw_filtering_data)
                # if filtering_data.operator == "<<":
                #     in_data[filtering_data.table][filtering_data.column]+=[filtering_data.value]
                # else:
                yield self._filtering_data_to_filtering_modifier(filtering_data)
            # yield self._in_data_to_in_modifier(in_data)

        return list(inner())

    def _in_data_to_in_modifier(self, in_data: dict[type[Base], dict[Column, list[any]]]):
        def modifier(query: Query):
            for table in in_data:
                for column in in_data[table]:
                    query = query.where(column.in_(in_data[table][column]))
            return query

        return modifier

    _FILTERING_REGEX = r"^[\d\s\W]*(?:(\w+?)[\s\W]*[.])?[\d\s\W]*(\w+?)[\s\W]*?([=><~!]+)(.*)$"

    @classmethod
    def _tag_data_to_filtering_data_raw(cls, tag_data: str):
        match = re.match(cls._FILTERING_REGEX, tag_data)
        if not match:
            raise ValueError(f'Invalid filtering tag data: {tag_data}')

        table, column, operator, value = match.groups()
        ic(table, column, operator, value)

        if column is None or operator is None or value is None:
            raise ValueError(f'Invalid filtering tag data: {tag_data}')

        return cls.FilteringDataRaw(table, column, operator, value)

    def _filtering_data_raw_to_filtering_data(self, data_raw: FilteringDataRaw) -> FilteringData:
        return self.FilteringData(
            table=(table_base := self._table_data_to_table(data_raw.table)),
            column=(column := self._column_data_to_column(table_base, data_raw.column)),
            operator=data_raw.operator,
            value=self._value_data_to_column_value(table_base, column, data_raw.value)
        )

    @classmethod
    def _filtering_data_to_filtering_modifier(cls, filtering_data: FilteringData):
        def modifier(query: Query):
            if filtering_data.operator == '=':
                return query.where(filtering_data.column == filtering_data.value)
            if filtering_data.operator == '!=':
                return query.where(filtering_data.column != filtering_data.value)
            if filtering_data.operator == '>':
                return query.where(filtering_data.column > filtering_data.value)
            if filtering_data.operator == '>=':
                return query.where(filtering_data.column >= filtering_data.value)
            if filtering_data.operator == '<':
                return query.where(filtering_data.column < filtering_data.value)
            if filtering_data.operator == '<=':
                return query.where(filtering_data.column <= filtering_data.value)
            if filtering_data.operator == '~':
                return query.where(filtering_data.column.like(f"%{filtering_data.value}%"))
            raise ValueError(f'Unknown operator: {filtering_data.operator}')

        return modifier

    def _table_data_to_table(self, table_data: str | None):
        if not table_data:
            return self.base_type
        return AlchemyExtras().get_table_by_name(table_data)

    @classmethod
    def _column_data_to_column(cls, table_base: type[Base], column_data: str):
        return AlchemyExtras().get_columns_of(table_base)[column_data]

    @classmethod
    def _value_data_to_column_value(cls, table_base: type[Base], column: Column, value: str):
        adapter = DataTypesAdapter(table_base)
        return adapter.adapt_types({column.key: value})[column.key]

    @dataclass
    class FilteringDataRaw:
        table: str
        column: str
        operator: str
        value: str

    @dataclass
    class FilteringData:
        table: type[Base]
        column: Column
        operator: str
        value: any

    @classmethod
    def _resolve_offset_tags_data(cls, tags_data: list[str]):
        return cls._tags_data_to_int(tags_data)

    @classmethod
    def _resolve_max_count_tags_data(cls, tags_data: list[str]):
        return cls._tags_data_to_int(tags_data)

    @classmethod
    def _tags_data_to_int(cls, tags_data: list[str]):
        one_tag_data = cls._take_one_tag_data(tags_data)
        return cls._cast_tag_data_to_int(one_tag_data)

    @classmethod
    def _take_one_tag_data(cls, tags: list[str], take_last=False):
        tag = tags[-1 if take_last else 0]
        return tag

    @classmethod
    def _cast_tag_data_to_int(cls, tag: str):
        return int(tag)
