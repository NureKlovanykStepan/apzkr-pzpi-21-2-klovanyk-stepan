from __future__ import annotations

from typing import Callable

from flask import Request
from flask_sqlalchemy.session import Session
from sqlalchemy.orm import Query

from app.database.models import Base
from app.utils.extra import ExtraValidatorsStorageBase, merge_chained
from app.services.creators.builders.weak_body import RequestWeakBodyBuilder, RequestType
from app.services.decorators.query_args.serialization import RequestArgsParser
from app.services.validators.base import BaseSessionAffectedValidator
from app.services.validators.crud import CRUDContext, CRUDBasicCreateValidator, CRUDBasicReadOrDeleteValidator, \
    CRUDBasicUpdateValidator, CreateValidationResult, ReadOrDeleteValidationResult, UpdateValidationResult


class RequestBodyFactory:
    def __init__(
            self, session: Session, model: type[Base], request: Request,
            extra_validators_storage: type[ExtraValidatorsStorageBase] | None = None
    ):
        self.session: Session = session
        self.model: type[Base] = model
        self.request: Request = request
        self.extra_validators_storage = extra_validators_storage

    def _get_default_body_builder_setup(self):
        return (RequestWeakBodyBuilder()
                .add_request(self.request)
                .add_model(self.model)
                .add_session(self.session)
                .add_extra_validation_storage(self.extra_validators_storage)
                )

    def get_crud_create_body(
            self, before_result_callback: Callable[[CreateValidationResult], None] | None = None,
            custom_validator: type[BaseSessionAffectedValidator[CRUDContext, any]] = CRUDBasicCreateValidator
    ):
        return (self._get_default_body_builder_setup()
                .add_type(RequestType.CREATE)
                .add_validator(custom_validator)
                .add_before_result_callback(before_result_callback)
                .build()
                )

    def get_crud_read_single_body(
            self, serialization_modifiers: RequestArgsParser.Result,
            before_result_callback: Callable[[ReadOrDeleteValidationResult], None] | None = None,
            custom_validator: type[BaseSessionAffectedValidator[CRUDContext, any]] = CRUDBasicReadOrDeleteValidator
    ):
        return (self._get_default_body_builder_setup()
                .add_type(RequestType.READ_SINGLE)
                .add_validator(custom_validator)
                .add_before_result_callback(before_result_callback)
                .add_serialization_modifiers(serialization_modifiers)
                .build()
                )

    def get_crud_read_many_body(
            self, serialization_modifiers: RequestArgsParser.Result,
            filter_on_query: Callable[[Query], Query],
            before_query_executed_callback: Callable[[Query], Query] = None
    ):
        filters_combined = merge_chained(before_query_executed_callback, filter_on_query)
        return (self._get_default_body_builder_setup()
                .add_type(RequestType.READ_MANY)
                .add_query_modification(filters_combined)
                .add_serialization_modifiers(serialization_modifiers)
                .build()
                )

    def get_crud_update_body(
            self, before_result_callback: Callable[[UpdateValidationResult], None] | None = None,
            custom_validator: type[BaseSessionAffectedValidator[CRUDContext, any]] = CRUDBasicUpdateValidator
    ):
        return (self._get_default_body_builder_setup()
                .add_type(RequestType.UPDATE)
                .add_validator(custom_validator)
                .add_before_result_callback(before_result_callback)
                .build()
                )

    def get_crud_delete_body(
            self, before_result_callback: Callable[[ReadOrDeleteValidationResult], None] | None = None,
            custom_validator: type[BaseSessionAffectedValidator[CRUDContext, any]] = CRUDBasicReadOrDeleteValidator
    ):
        return (self._get_default_body_builder_setup()
                .add_type(RequestType.DELETE)
                .add_validator(custom_validator)
                .add_before_result_callback(before_result_callback)
                .build()
                )
