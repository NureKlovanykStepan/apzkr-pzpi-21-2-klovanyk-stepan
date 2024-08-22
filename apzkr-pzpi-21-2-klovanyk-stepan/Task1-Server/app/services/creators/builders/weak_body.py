from __future__ import annotations

from enum import Enum
from http import HTTPStatus
from typing import Callable

from flask import Request
from flask_login import current_user
from flask_sqlalchemy.session import Session
from sqlalchemy.orm import Query

from app.database.models import Base, User
from app.utils.extra import CRUDResponse, AlchemyExtras, ExtraValidatorsStorageBase
from app.services.decorators.query_args.serialization import RequestArgsParser
from app.services.processors.tools import RequestHelper
from app.services.validators.base import BaseSessionAffectedValidator
from app.services.validators.crud import CRUDBasicCreateValidator, CRUDBasicReadOrDeleteValidator, \
    CRUDBasicUpdateValidator, CRUDContext, CreateValidationResult, UpdateValidationResult, ReadOrDeleteValidationResult


class RequestType(Enum):
    CREATE = ("create", CRUDBasicCreateValidator)
    READ_SINGLE = ("read", CRUDBasicReadOrDeleteValidator)
    UPDATE = ("update", CRUDBasicUpdateValidator)
    DELETE = ("delete", CRUDBasicReadOrDeleteValidator)
    READ_MANY = ("read_all", None)

    def __init__(self, name: str, validator: type[BaseSessionAffectedValidator]):
        self._value_ = (name, validator)

    def value(self) -> type[BaseSessionAffectedValidator]:
        return self._value_[1]


class RequestWeakBodyBuilder:
    def __init__(self):
        self.type: RequestType | None = None
        self.model: type[Base] | None = None
        self.before_result_callback: Callable[[any], None] | None = None
        self.request: Request | None = None
        self.session: Session | None = None
        self.serialization_modifiers: RequestArgsParser.Result | None = None
        self.query_mod: Callable[[Query], Query] | None = None
        self.validator: type[BaseSessionAffectedValidator[CRUDContext, any]] | None = None
        self.extra_validation_storage: type[ExtraValidatorsStorageBase] | None = None

    def add_type(self, type_: RequestType) -> RequestWeakBodyBuilder:
        self.type = type_
        return self

    def add_validator(self, validator: type[BaseSessionAffectedValidator[CRUDContext, any]]) -> RequestWeakBodyBuilder:
        self.validator = validator
        return self

    def add_model(self, model: type[Base]) -> RequestWeakBodyBuilder:
        self.model = model
        return self

    def add_request(self, request: Request):
        self.request = request
        return self

    def add_session(self, session: Session):
        self.session = session
        return self

    def add_extra_validation_storage(self, extra_validation_storage: type[ExtraValidatorsStorageBase] | None):
        self.extra_validation_storage = extra_validation_storage
        return self

    def add_query_modification(self, query_mod: Callable[[Query], Query]):
        self.query_mod = query_mod
        return self

    def add_serialization_modifiers(self, serialization_modifiers: RequestArgsParser.Result) -> RequestWeakBodyBuilder:
        self.serialization_modifiers = serialization_modifiers
        return self

    def add_before_result_callback(self, before_result_callback: Callable[[any], None]) -> RequestWeakBodyBuilder:
        self.before_result_callback = before_result_callback
        return self

    def _serializable_result(self, data: Base | list[Base], session: Session):
        if isinstance(current_user, User):
            bound_user = RequestHelper.get_current_bound_user(session, current_user)
        else:
            bound_user = None
        session.add_all(data if isinstance(data, list) else [data])
        return RequestHelper.get_general_serializer(
            data, self.serialization_modifiers, bound_user,
            session,
            self.extra_validation_storage
        ).serialize()

    def build(self) -> Callable[[], tuple[dict | str, HTTPStatus]]:
        assert self.session and self.model and self.type and self.request

        def result():
            if self.type == RequestType.READ_MANY:
                assert self.serialization_modifiers is not None
                query = self.session.query(self.model)
                if self.query_mod is not None:
                    query = self.query_mod(query)

                limit = query._limit_clause is not None and query._limit_clause.value
                offset = query._offset_clause is not None and query._offset_clause.value
                query._limit_clause = None
                query._offset_clause = None
                q = query.all()
                # ic(q.__len__(), limit, offset)
                return self._serializable_result(list(q)[offset:offset + limit] if limit else q, self.session)
                # return self._serializable_result(q, self.session)

            on_validation_success_main: Callable[[any], None] | None = None
            request_result: tuple[dict | str, HTTPStatus] | None = None

            if self.type == RequestType.CREATE:
                def on_validation_success_main(result: CreateValidationResult):
                    RequestHelper.insert_into_db(self.session, result.object_to_create)
                    nonlocal request_result
                    request_result = CRUDResponse.CREATED.embed_pk_data_from_object(
                        result.object_to_create,
                        self.model.__name__
                    )
            elif self.type == RequestType.UPDATE:
                def on_validation_success_main(result: UpdateValidationResult):
                    nonlocal request_result
                    pk_cols = AlchemyExtras().get_pk_of(self.model)
                    merged_data = {}
                    for col in pk_cols:
                        if col.key in result.object_new_data:
                            merged_data[col.key] = result.object_new_data[col.key]
                        else:
                            merged_data[col.key] = getattr(result.object_to_update, col.key)
                    RequestHelper.update_to_db(self.session, result.object_to_update, result.object_new_data)
                    request_result = CRUDResponse.UPDATED.embed_pk_data(merged_data, self.model.__name__)
            elif self.type == RequestType.DELETE:
                def on_validation_success_main(result: ReadOrDeleteValidationResult):
                    RequestHelper.delete_from_db(self.session, result.object)
                    nonlocal request_result
                    request_result = CRUDResponse.DELETED.embed_pk_data_from_object(result.object, self.model.__name__)
            elif self.type == RequestType.READ_SINGLE:
                def on_validation_success_main(result: ReadOrDeleteValidationResult):
                    assert self.serialization_modifiers is not None
                    nonlocal request_result
                    request_result = self._serializable_result(result.object, self.session)

            assert on_validation_success_main

            def on_validation_success_result_callback(result: any):
                if self.before_result_callback:
                    self.before_result_callback(result)
                on_validation_success_main(result)

            self.validator(self.session, on_validation_success_result_callback).validate(
                CRUDContext(model=self.model, request=self.request)
            )

            return request_result

        return result
