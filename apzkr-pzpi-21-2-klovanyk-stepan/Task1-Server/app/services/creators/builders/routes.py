from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntFlag
from functools import reduce
from typing import Callable

from flask import Blueprint, request, Response
from flask_login import login_required, current_user
from sqlalchemy.orm import Query, Session

from app import Globals
from app.database.models import Base, User
from app.utils.extra import ExtraValidatorsStorageBase, AlchemyExtras, ValidatorsData, \
    _ExtraValidatorsStorageBaseSingleton
from app.services.creators.factories.body_details import BodyFactoryDetails, BodyFactoryDetailsFactory
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import serialization_args
from app.services.decorators.general.permissions import RequiredPermissionsFlag, permissions_of_employee_required
from app.services.processors.tools import RequestHelper
from app.services.validators.base import ValidationException, BaseSessionAffectedValidator
from app.services.validators.crud import CRUDContext, CreateValidationResult, UpdateValidationResult, \
    ReadOrDeleteValidationResult


class RoutesBuilder[BaseModel: Base]:
    def __init__(self, blueprint: Blueprint, base_type: type[BaseModel]):
        self.blueprint = blueprint
        self.route = '/'
        self.body: Callable
        self.permissions: RequiredPermissionsFlag = RequiredPermissionsFlag.NONE
        self.modifiers: 'RequestModifiers' = RequestModifiers.NONE
        self.base = base_type
        self._counter = 0
        self._current_extra_validators_ds: type[ExtraValidatorsStorageBase] | None = None
        self._preserved_extra_validators_ds: type[_ExtraValidatorsStorageBaseSingleton] | None = None

    def _associate_route(self, func, methods: list[str]):
        self._counter += 1
        self.blueprint.add_url_rule(
            rule=self.route,
            endpoint=f'{self.blueprint.root_path}_{self._counter}_{'-'.join(methods)}',
            view_func=func,
            methods=methods
        )
        self.blueprint.add_url_rule(
            rule=self.route.rstrip('/'),
            endpoint=f'{self.blueprint.root_path}_{self._counter}_{'-'.join(methods)}',
            view_func=func,
            methods=methods
        )

    def _inject_error_handler(self, code_or_exception: int | type[Exception], func):
        self.blueprint.register_error_handler(code_or_exception, func)

    def inject_ExceptionsHandler(self, exception: type[Exception], func):
        self._inject_error_handler(exception, func)
        return self

    def inject_CodeHandler(self, code: int, func):
        self._inject_error_handler(code, func)
        return self

    def useDefault_ValidationExceptionHandler(self):
        self.inject_ExceptionsHandler(ValidationException, self._validation_exception_handler)
        return self

    def use_ValidationDataStorage(
            self, validation_data_storage: type[ExtraValidatorsStorageBase]
    ):
        self._current_extra_validators_ds = validation_data_storage
        return self

    def use_NoValidationDataStorage(self):
        self._current_extra_validators_ds = None
        return self

    def extraValidators_SnapshotStorage(self):
        current_storage = self._current_extra_validators_ds
        if current_storage is None:
            return
        if not issubclass(current_storage, _ExtraValidatorsStorageBaseSingleton):
            raise Exception('Can only snapshot _ExtraValidatorsStorageBaseSingleton instances')
        if self._preserved_extra_validators_ds is not None:
            raise Exception('Snapshot is already in usage')

        self._current_extra_validators_ds = current_storage().snapshot()
        self._preserved_extra_validators_ds = current_storage

        return self

    def extraValidators_RestoreLiveStorage(self):
        if self._preserved_extra_validators_ds is None:
            raise Exception('Snapshot has not been done before')
        self._current_extra_validators_ds = self._preserved_extra_validators_ds
        self._preserved_extra_validators_ds = None
        return self

    def extract_PermissionsAsUserExtraValidation(self, storage: ExtraValidatorsStorageBase):
        perms = self.permissions

        def user_permission_validator(bound_user: User):
            try:
                permissions_of_employee_required(bound_user, perms)(lambda: None)()
            except ValidationException as e:
                return e

        storage[self.base].extend_UserValidator(user_permission_validator, True)
        return self

    def edit_ValidationStorageEntry(
            self,
            editing_callback: Callable[[ValidatorsData[Base, User]], None]
    ):
        editing_callback(self._current_extra_validators_ds()[self.base])
        return self

    @staticmethod
    def _validation_exception_handler(validation_exception: ValidationException):
        return str(validation_exception), validation_exception.http_status_code

    @dataclass
    class Decorators:
        decorators: list[Callable[[Callable], Callable]] = field(default_factory=list)

        def add(self, wrapper: Callable[[Callable], Callable]):
            self.decorators.insert(0, wrapper)

        def apply(self, func: Callable):
            return reduce(lambda ex, wr: wr(ex), self.decorators, func)

    def _build_decorators_from_modifiers(self):
        decorators = self.Decorators()
        if self.modifiers & RequestModifiers.LOGIN:
            decorators.add(login_required)
        if self.modifiers & RequestModifiers.PERMISSIONS:
            decorators.add(permissions_of_employee_required(current_user, self.permissions))
        if self.modifiers & RequestModifiers.SERIALIZATION:
            decorators.add(serialization_args(request, self.base))
        if self.modifiers & RequestModifiers.FILTERING:
            decorators.add(filtering_args(request, self.base))
        if self.modifiers & RequestModifiers.GLOBAL_COMPANY:
            decorators.add(self._global_company_check_deco(current_user))
        return decorators

    @staticmethod
    def _global_company_check_deco(user: User):
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                with Globals().db.session() as session:
                    bound_user = RequestHelper.get_current_bound_user(session, user)
                    RequestHelper.validate_global_company_of_employee(bound_user.employee)
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def buildRequest_onValidator[T, S](
            self,
            validator: type[BaseSessionAffectedValidator[CRUDContext, T]],
            body: Callable[[dict[str, str]], Callable[[T], S]],
            methods: list[str]
    ):
        wrappers = self._build_decorators_from_modifiers()

        def executor(**kwargs):
            with Globals().db.session() as session:
                result: S

                def success(data: T):
                    nonlocal result
                    result = body(kwargs)(data)

                validator(session, body, success).validate(request)
                return result

        wrapped_executor = wrappers.apply(executor)
        self._associate_route(func=wrapped_executor, methods=methods)

        return self

    def buildRequest_onBodyFactory(
            self,
            factory_utilize: Callable[
                [BodyFactoryDetailsFactory], BodyFactoryDetails
            ],
            result_modifier: Callable[[any, dict[str, any]], any] = lambda x, y: x,
            methods: list[str] = None
    ):
        wrappers_baked = self._build_decorators_from_modifiers()
        extra_validators_baked = self._current_extra_validators_ds

        def get_advanced_factory_details(provided_session: Session | None):
            factory = BodyFactoryDetailsFactory(
                extra_validators_data_storage=extra_validators_baked, base_type=self.base,
                session=provided_session
            )
            return factory_utilize(factory)

        def executor(**kwargs):
            with Globals().db.session() as session_:
                kwargs['session'] = session_
                return result_modifier(
                    get_advanced_factory_details(session_).init_factory(self.base, session_, request).get_body_creator(
                        kwargs
                    )(),
                    kwargs
                )

        wrapped_executor = wrappers_baked.apply(executor)
        self._associate_route(
            func=wrapped_executor,
            methods=methods or [get_advanced_factory_details(None).method]
        )
        return self

    class AdvancedDetailsBase[T, R](ABC):
        def __init__(self):
            pass

        @abstractmethod
        def details_provider(self, body_factory_details_factory: BodyFactoryDetailsFactory) \
                -> Callable[[Callable[[T, dict[str, any]], R]], BodyFactoryDetails]:
            return NotImplemented()

        def _callback_data_recorder(self, result: T, request_args: dict[str, any]):
            return self.before_result_callback(result, request_args['session'], request_args)

        @abstractmethod
        def before_result_callback(self, result: T, session: Session, request_args: dict[str, any]) -> R:
            return NotImplemented()

        @abstractmethod
        def response_mod(self, response: any, session: Session, request_data: dict[str, any]) -> dict | Response:
            return NotImplemented()

        @abstractmethod
        def methods_provider(self) -> list[str]:
            return NotImplemented()

        def compose(self):
            details_provider = self.details_provider
            before_result_callback = self._callback_data_recorder
            methods_provider = self.methods_provider
            response_mod = self.response_mod

            class ComposedDetails:
                def __init__(self):
                    self.factory_utilize: Callable[
                        [BodyFactoryDetailsFactory], BodyFactoryDetails
                    ] = lambda x: details_provider(x)(before_result_callback)
                    self.response_mod: Callable[
                        [any, dict[str, any]], any
                    ] = lambda response_data, request_args: response_mod(
                        response_data,
                        request_args['session'],
                        request_args
                    )
                    self.methods: list[str] = methods_provider()

            return ComposedDetails()

    def buildRequest_onBodyFactoryAdvanced[T, R](
            self, advanced_details: type[AdvancedDetailsBase[T, R]]
    ):
        composed = advanced_details().compose()
        return self.buildRequest_onBodyFactory(
            composed.factory_utilize,
            composed.response_mod,
            composed.methods
        )

    def useDefault_CreateRequest(
            self,
            on_validation_success: Callable[[CreateValidationResult, dict[str, any]], None] = None
    ):
        def utilize_factory(adf: BodyFactoryDetailsFactory):
            return adf.CREATE(on_validation_success)

        (self.route_Reset())

        return self.buildRequest_onBodyFactory(
            utilize_factory
        )

    def useDefault_UpdateRequest(
            self,
            on_validation_success: Callable[[UpdateValidationResult, dict[str, any]], None] = None
    ):
        def utilize_factory(adf: BodyFactoryDetailsFactory):
            return adf.UPDATE(on_validation_success)

        pk_data = sorted([pk.key for pk in AlchemyExtras().get_pk_of(self.base)])
        self.route_Reset()
        [self.route_AppendVariable(pk) for pk in pk_data]

        return self.buildRequest_onBodyFactory(
            utilize_factory
        )

    def useDefault_DeleteRequest(
            self,
            on_validation_success: Callable[[ReadOrDeleteValidationResult, dict[str, any]], None] = None
    ):
        def utilize_factory(adf: BodyFactoryDetailsFactory):
            return adf.DELETE(on_validation_success)

        pk_data = sorted([pk.key for pk in AlchemyExtras().get_pk_of(self.base)])
        self.route_Reset()
        [self.route_AppendVariable(pk) for pk in pk_data]

        return self.buildRequest_onBodyFactory(
            utilize_factory
        )

    def useDefault_ReadSingleRequest(
            self,
            on_validation_success: Callable[[ReadOrDeleteValidationResult, dict[str, any]], None] = None
    ):
        def utilize_factory(adf: BodyFactoryDetailsFactory):
            return adf.READ_ONE(on_validation_success)

        pk_data = sorted([pk.key for pk in AlchemyExtras().get_pk_of(self.base)])
        (self
         .route_Reset()
         .modifiers_Use(RequestModifiers.SERIALIZATION))
        [self.route_AppendVariable(pk) for pk in pk_data]

        return self.buildRequest_onBodyFactory(
            utilize_factory
        )

    def useDefault_ReadManyRequest(
            self,
            query_mod: Callable[[Query, dict[str, any]], Query] = None
    ):
        def utilize_factory(adf: BodyFactoryDetailsFactory):
            return adf.READ_MANY(query_mod)

        (self
         .route_Reset()
         .modifiers_Use(RequestModifiers.SERIALIZATION)
         .modifiers_Use(RequestModifiers.FILTERING))

        return self.buildRequest_onBodyFactory(
            utilize_factory
        )

    def route_AppendCategory(self, route: str):
        if '<' in route or '>' in route:
            raise Exception('Route can not contain < or >. Use routeAppendVariable instead.')
        self.route = f'{self.route}{route.strip("/")}/'
        return self

    def route_AppendVariable(self, variable_name: str):
        self.route = f'{self.route}<{variable_name}>/'
        return self

    def route_Reset(self):
        self.route = '/'
        return self

    def route_Builder(self):
        class LocalRouteBuilder:
            def __init__(self, routes_builder: RoutesBuilder):
                self.final_route = ""
                self.routes_builder = routes_builder

            def category(self, category: str):
                self.final_route = f'/{self.final_route.strip("/")}/{category}/'
                return self

            def variable(self, variable_name: str):
                self.final_route = f'/{self.final_route.strip("/")}/<{variable_name}>/'
                return self

            def cat(self, category: str):
                return self.category(category)

            def var(self, variable_name: str):
                return self.variable(variable_name)

            def build(self):
                self.routes_builder.route = self.final_route
                return self.routes_builder

        return LocalRouteBuilder(self)

    def permissions_Set(self, permissions: RequiredPermissionsFlag):
        self.permissions = permissions
        self._permissions_auto_modifier_manager()
        return self

    def permissions_Clear(self):
        self.permissions = RequiredPermissionsFlag.NONE
        self._permissions_auto_modifier_manager()
        return self

    def _permissions_auto_modifier_manager(self):
        if self.permissions != 0:
            self.modifiers_Use(RequestModifiers.PERMISSIONS)
        else:
            self.modifiers_Remove(RequestModifiers.PERMISSIONS)
        return self

    def modifiers_Use(self, modifiers: 'RequestModifiers'):
        self.modifiers |= modifiers
        return self

    def modifiers_Remove(self, modifiers: 'RequestModifiers'):
        self.modifiers &= ~modifiers
        return self

    def modifiers_Clear(self):
        self.modifiers = 0
        return self


class RequestModifiers(IntFlag):
    NONE = 0,
    SERIALIZATION = 1
    FILTERING = 2
    LOGIN = 4
    PERMISSIONS = 8
    GLOBAL_COMPANY = 16
