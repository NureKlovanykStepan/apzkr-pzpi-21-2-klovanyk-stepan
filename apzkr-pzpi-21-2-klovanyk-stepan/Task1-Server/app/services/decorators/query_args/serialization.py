import functools
from dataclasses import dataclass

from flask import Request
from sqlalchemy import Column

from app.database.models import Base
from app.utils.extra import AlchemyExtras


class RequestArgsParser:
    delimiter = ','

    @dataclass
    class TableColumnSpec:
        table: str | None = None
        column: str | None = None

    @dataclass
    class Result:
        included_columns: set[Column]
        included_tables: set[type[Base]]
        excluded_columns: set[Column]
        excluded_tables: set[type[Base]]

    def __new__(cls, request_args: dict, base_model: type[Base] = None):
        include_raw_args = request_args.get('I') or ''
        exclude_raw_args = request_args.get('E') or ''
        base_model = base_model

        return cls.Result(
            *cls.specs_to_data(cls.cast_to_specs(cls.separate(include_raw_args)), base_model),
            *cls.specs_to_data(cls.cast_to_specs(cls.separate(exclude_raw_args)), base_model)
        )

    @classmethod
    def separate(cls, raw_args: str):
        return [s.strip() for s in raw_args.split(cls.delimiter)]

    @classmethod
    def cast_to_specs(cls, separated_args: list[str]):
        return [cls.TableColumnSpec(*s.split('.')) for s in separated_args]

    @classmethod
    def specs_to_data(cls, specifiers: list[TableColumnSpec], base_model: type[Base]):
        columns: set[Column] = set()
        tables: set[type[Base]] = set()

        def extract_table(table_name):
            try:
                return AlchemyExtras().get_table_by_name(table_name)
            except KeyError:
                raise (KeyError(f'Table {table_name} does not exist'))

        def extract_column(model: type[Base], column_name):
            try:
                return AlchemyExtras().get_columns_of(model)[column_name]
            except KeyError:
                raise KeyError(f'Column {column_name} does not exist in {model.__tablename__}')

        for specifier in specifiers:
            if not (table := specifier.table):
                continue
            if not (column := specifier.column):
                try:
                    tables.add(extract_table(table))
                    continue
                except KeyError:
                    columns.add(extract_column(base_model, table))
                    continue
            columns.add(extract_column(extract_table(table), column))

        return columns, tables


def serialization_args(request: Request, base_model: type[Base]):
    """
    Decorator function that adds:
        serialization_modifiers_data: :class:`SerializationRequestArgsParser.Result`
    to the wrapped function.

    Syntax example::

        .../api/.../route?I=table1.column1,table2,column3&E=...

        table1.column1 - include only column1 from table1
        table2 - include all columns from table2
        column3 - include only column3 from base_model

    """

    def Decorator(func):
        @functools.wraps(func)
        def Wrapper(*args, **kwargs):
            return func(
                *args, serialization_modifiers=RequestArgsParser(
                    request.args, base_model
                ), **kwargs
            )

        return Wrapper

    return Decorator
