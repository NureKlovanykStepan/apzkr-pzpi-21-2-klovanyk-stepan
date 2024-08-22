from http import HTTPStatus
from typing import Callable

from flask import Request
from flask_login import current_user
from icecream import ic
from sqlalchemy.orm import Session, Query

from app.database.models import Base, User
from app.utils.extra import ExtraValidatorsStorageBase, merge_callbacks, combined_injected_validation, \
    ValidatorsData, merge_chained
from app.services.creators.factories.body import RequestBodyFactory
from app.services.validators.crud import CreateValidationResult, UpdateValidationResult, \
    ReadOrDeleteValidationResult


class BodyFactoryDetails[Extension, Factory]:
    def __init__(
            self,
            accepted_extension: Extension,
            response_key_args: list[str],
            factory_type: type[Factory],
            factory_method: Callable[[Factory, any, Extension], Callable[[], tuple[str | None,
            HTTPStatus]]],
            method: str,
            extra_validators_storage: type[ExtraValidatorsStorageBase]
    ):
        self.accepted_extension = accepted_extension
        self.response_key_args = response_key_args
        self.factory_type = factory_type
        self.factory_method = factory_method
        self.method = method
        self.extra_validators_storage = extra_validators_storage

    class Inited:
        def __init__(self, factory: RequestBodyFactory, details: 'BodyFactoryDetails'):
            self.details = details
            self.factory = factory

        def get_body_creator(self, request_method_kwargs: dict):
            def request_argless(data):
                return self.details.accepted_extension(data, request_method_kwargs)
            return self.details.factory_method(
                self.factory,
                *[request_method_kwargs[k] for k in self.details.response_key_args],
                (None if not self.details.accepted_extension else request_argless),
            )

    def init_factory(
            self,
            model: type[Base],
            session: Session,
            request: Request,
    ):
        return self.Inited(self.factory_type(session, model, request, self.extra_validators_storage), self)


class BodyFactoryDetailsFactory:
    def __init__(
            self,
            extra_validators_data_storage: type[ExtraValidatorsStorageBase],
            base_type: type[Base],
            session: Session
    ):
        self._extra_validation_factory = (
                extra_validators_data_storage
                and self.ExtraValidationCallbackFactory(extra_validators_data_storage()[base_type], session)
                or None
        )
        self._extra_validators_data_storage = extra_validators_data_storage

    class ExtraValidationCallbackFactory:
        def __init__(self, extra_validation_data: ValidatorsData[Base, User], session: Session):
            self._extra_validation_data = extra_validation_data
            self._session = session

        def _validator_universal(self) \
                -> Callable[[Base, dict[str, any] | None], None]:
            data = self._extra_validation_data
            return lambda obj_, new_data_: combined_injected_validation(
                data,
                current_user,
                obj_,
                self._session,
                new_data_,
            )

        def for_CreateValidationResult(self):
            validator = self._validator_universal()

            def callback(result: CreateValidationResult, request_args: dict[str, any]):
                validator(result.object_to_create, None)

            return callback

        def for_UpdateValidationResult(self):
            validator = self._validator_universal()

            def callback(result: UpdateValidationResult, request_args: dict[str, any]):
                validator(result.object_to_update, result.object_new_data)

            return callback

        def for_ReadOrDeleteValidationResult(self):
            validator = self._validator_universal()

            def callback(result: ReadOrDeleteValidationResult, request_args: dict[str, any]):
                validator(result.object, None)

            return callback

        def for_Query(self):
            data = self._extra_validation_data

            def callback(result: Query, request_args: dict[str, any]):
                data.validate_User(current_user, self._session)
                return result

            return callback

    def CREATE(self, before_result_callback: Callable[[CreateValidationResult, dict[str, any]], None] = None):
        return BodyFactoryDetails(
            merge_callbacks(
                self._extra_validation_factory and self._extra_validation_factory.for_CreateValidationResult(),
                before_result_callback
            ),
            [],
            RequestBodyFactory,
            RequestBodyFactory.get_crud_create_body,
            "POST",
            self._extra_validators_data_storage
        )

    def UPDATE(self, before_result_callback: Callable[[UpdateValidationResult, dict[str, any]], None] = None):
        return BodyFactoryDetails(
            merge_callbacks(
                self._extra_validation_factory and self._extra_validation_factory.for_UpdateValidationResult(),
                before_result_callback
            ),
            [],
            RequestBodyFactory,
            RequestBodyFactory.get_crud_update_body,
            "PUT",
            self._extra_validators_data_storage
        )

    def DELETE(self, before_result_callback: Callable[[ReadOrDeleteValidationResult, dict[str, any]], None] = None):
        return BodyFactoryDetails(
            merge_callbacks(
                self._extra_validation_factory and self._extra_validation_factory.for_ReadOrDeleteValidationResult(),
                before_result_callback
            ),
            [],
            RequestBodyFactory,
            RequestBodyFactory.get_crud_delete_body,
            "DELETE",
            self._extra_validators_data_storage
        )

    def READ_ONE(self, before_result_callback: Callable[[ReadOrDeleteValidationResult, dict[str, any]], None] = None):
        return BodyFactoryDetails(
            merge_callbacks(
                self._extra_validation_factory and self._extra_validation_factory.for_ReadOrDeleteValidationResult(),
                before_result_callback
            ),
            ["serialization_modifiers"],
            RequestBodyFactory,
            RequestBodyFactory.get_crud_read_single_body,
            "GET",
            self._extra_validators_data_storage
        )

    def READ_MANY(self, extra_query_mod: Callable[[Query, dict[str, any]], Query] = None):
        return BodyFactoryDetails(
            merge_chained(
                self._extra_validation_factory and self._extra_validation_factory.for_Query(),
                extra_query_mod
                ),
            ["serialization_modifiers", "filtering_query_mod"],
            RequestBodyFactory,
            RequestBodyFactory.get_crud_read_many_body,
            "GET",
            self._extra_validators_data_storage
        )
