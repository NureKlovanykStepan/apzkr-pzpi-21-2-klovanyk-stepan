import datetime
from dataclasses import dataclass
from http import HTTPStatus

from flask import Request
from flask_sqlalchemy.session import Session
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from app import Globals
from app.database.models import Base, User
from app.utils.extra import AlchemyExtras
from app.services.validators.base import (ValidationExceptionType, BasicPhoneNumberLengthValidator,
                                          BasicEmailValidator, \
    BaseDataConverter, ValidationException, BaseValidator, BaseSessionAffectedValidator)


class RequestJsonTypeValidator(BaseValidator[Request, dict]):
    def _validation_body(self, context: Request) -> dict:
        try:
            return context.get_json()
        except BadRequest as e:
            raise ValidationException(ValidationExceptionType.INVALID_JSON, HTTPStatus.BAD_REQUEST, str(e))
        except UnsupportedMediaType as e:
            raise ValidationException(ValidationExceptionType.INVALID_JSON, HTTPStatus.UNSUPPORTED_MEDIA_TYPE, str(e))


class DummyDataConverter(BaseDataConverter):
    def convert(self) -> dict[str, any]:
        return self.unconverted

    def get_conversion_fields_mapping(self) -> dict[str, str]:
        return {}


class UserDataConverter(BaseDataConverter):
    def convert(self):
        converted = {}
        for key, value in self.unconverted.items():
            if key == "password":
                converted["password_hash"] = Globals().bcrypt.generate_password_hash(value).decode("utf-8")
            elif key == "phone_number":
                BasicPhoneNumberLengthValidator().validate(value)
                converted["phone_number"] = value
            elif key == "email":
                BasicEmailValidator().validate(value)
                converted["email"] = value
            else:
                converted[key] = value
        return converted

    def get_conversion_fields_mapping(self) -> dict[str, str]:
        return {"password": "password_hash"}


class DataTypesAdapter:
    def __init__(self, model: type[Base]):
        self.model = model

    def adapt_types(self, data: dict[str, any]) -> dict[str, any]:
        all_columns = AlchemyExtras().get_columns_of(self.model)
        for column_name, column in all_columns.items():
            if column_name in data.keys():
                if column.type.python_type == datetime.datetime:
                    continue
                elif data[column_name] is None and column.nullable:
                    continue
                else:
                    data[column_name] = column.type.python_type(data[column_name])
        return data


class DataConvertersFactory:
    @staticmethod
    def get_data_converter(data_type: type[Base]) -> type[BaseDataConverter]:
        if data_type == User:
            return UserDataConverter
        else:
            return DummyDataConverter


@dataclass
class ConvertedDataTypesUnmatched:
    data: dict[str, any]
    model: type[Base]


@dataclass
class ConvertedData:
    data: dict[str, any]
    model: type[Base]


class RawJsonDataConversionValidator(BaseValidator[dict, ConvertedDataTypesUnmatched]):
    def __init__(self, model: type[Base], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model

    def _validation_body(self, context: dict) -> ConvertedData:
        converter = DataConvertersFactory.get_data_converter(self.model)
        try:
            return ConvertedData(converter(context).convert(), self.model)
        except ValidationException as e:
            raise ValidationException(ValidationExceptionType.RAW_JSON_CONVERSION_EXCEPTION, HTTPStatus.BAD_REQUEST, e)


class TypesAdapterValidator(BaseValidator[ConvertedDataTypesUnmatched, ConvertedData]):
    def _validation_body(self, context: ConvertedDataTypesUnmatched) -> ConvertedData:
        adapter = DataTypesAdapter(context.model)
        try:
            return ConvertedData(adapter.adapt_types(context.data), context.model)
        except ValueError as e:
            raise ValidationException(ValidationExceptionType.TYPES_CONVERSION_EXCEPTION, HTTPStatus.BAD_REQUEST, e)


class IntegrityRedundantFieldsValidator(BaseValidator[ConvertedData, ConvertedData]):
    def _validation_body(self, context: ConvertedData) -> ConvertedData:
        all_columns = AlchemyExtras().get_columns_of(context.model)
        all_relationships = AlchemyExtras().get_relationships_of(context.model)
        for key in context.data.keys():
            if key in all_relationships:
                raise ValidationException(
                    ValidationExceptionType.DIRECT_RELATIONSHIPS_UNSUPPORTED, HTTPStatus.BAD_REQUEST, key
                )
            if key not in all_columns:
                raise ValidationException(
                    ValidationExceptionType.REQUEST_BODY_UNKNOWN_FIELD, HTTPStatus.BAD_REQUEST, key
                )
        return context


class IntegrityAllFieldsPresenceValidator(BaseValidator[ConvertedData, ConvertedData]):
    def __init__(self, force_add_nullables: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.force_add_nullables = force_add_nullables

    def _validation_body(self, context: ConvertedData) -> ConvertedData:
        all_columns = AlchemyExtras().get_columns_of(context.model)
        for column_name, column in all_columns.items():
            if context.data.get(column_name) is None and self.force_add_nullables and column.nullable:
                context.data[column_name] = None
                continue

            if column.autoincrement:
                continue

            if column_name not in context.data.keys():
                raise ValidationException(
                    ValidationExceptionType.REQUEST_BODY_MISSING_FIELD, HTTPStatus.BAD_REQUEST, f'{column_name} not found'
                )
        return context


class IntegrityPrimaryKeyPresenceValidator(BaseValidator[ConvertedData, ConvertedData]):
    def _validation_body(self, context: ConvertedData) -> ConvertedData:
        primary_key = AlchemyExtras().get_pk_of(context.model)
        for column in primary_key:
            if column.key not in context.data.keys():
                raise ValidationException(
                    ValidationExceptionType.REQUEST_BODY_MISSING_PK, HTTPStatus.BAD_REQUEST, column
                )
        return context


class ExistencePrimaryKeyValidator(BaseSessionAffectedValidator[ConvertedData, tuple[ConvertedData, Base]]):
    def _validation_body(self, context: ConvertedData) -> tuple[ConvertedData, Base]:
        primary_key = AlchemyExtras().get_pk_of(context.model)
        primary_key_data = {column.key: context.data[column.key] for column in primary_key if
                            column.key in context.data}

        if (found_object := self.session.get(context.model, primary_key_data)) is None:
            raise ValidationException(
                ValidationExceptionType.PK_OBJECT_NOT_FOUND, HTTPStatus.BAD_REQUEST, f'{primary_key} not found'
            )
        return context, found_object


class NonExistencePrimaryKeyValidator(BaseSessionAffectedValidator[ConvertedData, ConvertedData]):
    def __init__(self, session: Session, excluded_pk_from_header: dict[str, any] | None = None, *args, **kwargs):
        super().__init__(session, *args, **kwargs)
        self.excluded_pk_from_header = excluded_pk_from_header

    def _validation_body(self, context: ConvertedData) -> ConvertedData:
        primary_key = AlchemyExtras().get_pk_of(context.model)
        primary_key_data = {column.key: context.data[column.key] for column in primary_key if
                            column.key in context.data}
        if len(primary_key_data) == 0 or self.excluded_pk_from_header == primary_key_data:
            return context

        if len(primary_key_data) != len(primary_key):
            required = set(column.key for column in primary_key)
            missing = required-set(primary_key_data.keys())
            raise ValidationException(
                ValidationExceptionType.PK_FIELDS_COUNT_MISMATCH, HTTPStatus.BAD_REQUEST, f'Missing fields {missing} for '
                                                                                      f'PK {required}'
            )

        if self.session.get(context.model, primary_key_data) is not None:
            raise ValidationException(
                ValidationExceptionType.PK_OBJECT_ALREADY_EXISTS, HTTPStatus.BAD_REQUEST, f'{primary_key} already exists'
            )
        return context


class ExistenceForeignKeysValidator(BaseSessionAffectedValidator[ConvertedData, ConvertedData]):
    def _validation_body(self, context: ConvertedData) -> ConvertedData:
        all_relationships = AlchemyExtras().get_relationships_of(context.model)
        relationships_data = [pair for relationship in all_relationships for pair in
                              AlchemyExtras().get_relationship_parent_and_child_pairs(relationship)]
        parents_and_children = {child: parent for parent, child in relationships_data if child.key in context.data}
        foreign_keys_data = {column: context.data[column.key] for column in parents_and_children}
        for child, value in foreign_keys_data.items():
            parent = parents_and_children[child]
            if self.session.get(AlchemyExtras().get_table_by_name(parent.table.name), {parent.key: value}) is None:
                raise ValidationException(
                    ValidationExceptionType.PARENT_OBJECT_NOT_FOUND, HTTPStatus.BAD_REQUEST, child
                )
        return context


class MarshmallowLoadValidator(BaseSessionAffectedValidator[ConvertedData, Base]):
    def _validation_body(self, context: ConvertedData) -> Base:
        schema = AlchemyExtras().get_schema_of(context.model)
        try:
            return schema(session=self.session).load(context.data)
        except Exception as e:
            raise ValidationException(
                ValidationExceptionType.MARSHMALLOW_VALIDATION_EXCEPTION, HTTPStatus.BAD_REQUEST, e
            )


@dataclass
class CRUDContext:
    model: type[Base]
    request: Request


@dataclass
class CreateValidationResult:
    object_to_create: Base


class CRUDBasicCreateValidator(BaseSessionAffectedValidator[CRUDContext, CreateValidationResult]):

    def _validation_body(self, context: CRUDContext) -> CreateValidationResult:
        object_to_create: Base | None = None

        def on_validation_success(new_object: Base):
            nonlocal object_to_create
            object_to_create = new_object

        body_validators = RequestJsonTypeValidator()
        body_validators.set_next(RawJsonDataConversionValidator(context.model)).set_next(
            TypesAdapterValidator()
            ).set_next(IntegrityRedundantFieldsValidator()).set_next(IntegrityAllFieldsPresenceValidator()).set_next(
            NonExistencePrimaryKeyValidator(self.session)
            ).set_next(ExistenceForeignKeysValidator(self.session)).set_next(
            MarshmallowLoadValidator(self.session, on_validation_success)
            )

        try:
            body_validators.validate(context.request)
        except ValidationException as e:
            raise ValidationException(ValidationExceptionType.CREATE_VALIDATION_EXCEPTION, HTTPStatus.BAD_REQUEST, e)

        assert object_to_create is not None

        return CreateValidationResult(object_to_create)


@dataclass
class ReadOrDeleteValidationResult:
    object: Base


class CRUDBasicReadOrDeleteValidator(BaseSessionAffectedValidator[CRUDContext, ReadOrDeleteValidationResult]):

    def _validation_body(self, context: CRUDContext) -> ReadOrDeleteValidationResult:
        final_object: Base | None = None

        def on_validation_success(data: tuple[ConvertedData, Base]):
            nonlocal final_object
            final_object = data[1]

        header_validators = RawJsonDataConversionValidator(context.model)
        header_validators.set_next(
            TypesAdapterValidator()
        ).set_next(
            IntegrityPrimaryKeyPresenceValidator()
        ).set_next(
            ExistencePrimaryKeyValidator(
                self.session, on_validation_success
            )
        )

        try:
            header_validators.validate(context.request.view_args)
        except ValidationException as e:
            raise ValidationException(ValidationExceptionType.READ_VALIDATION_EXCEPTION, HTTPStatus.BAD_REQUEST, e)

        assert final_object is not None

        return ReadOrDeleteValidationResult(final_object)


@dataclass
class UpdateValidationResult:
    object_new_data: dict[str, any]
    object_to_update: Base


class CRUDBasicUpdateValidator(BaseSessionAffectedValidator[CRUDContext, UpdateValidationResult]):
    def _validation_body(self, context: CRUDContext) -> UpdateValidationResult:
        data_to_update: dict[str, any] = {}
        object_to_update: Base | None = None

        def on_header_validation_success(data: tuple[ConvertedData, Base]):
            nonlocal object_to_update
            object_to_update = data[1]

        def on_body_validation_success(data: ConvertedData):
            nonlocal data_to_update
            data_to_update = data.data

        header_validators = RawJsonDataConversionValidator(context.model)
        header_validators.set_next(TypesAdapterValidator()).set_next(
            IntegrityPrimaryKeyPresenceValidator()
        ).set_next(
            ExistencePrimaryKeyValidator(self.session, on_header_validation_success)
        )

        body_validators = RequestJsonTypeValidator()
        body_validators_cont = body_validators.set_next(RawJsonDataConversionValidator(context.model)).set_next(
            TypesAdapterValidator()
        ).set_next(
            IntegrityRedundantFieldsValidator()
        )

        try:
            header_validators.validate(context.request.view_args)
            body_validators_cont.set_next(
                NonExistencePrimaryKeyValidator(
                    self.session, excluded_pk_from_header={col.key: getattr(object_to_update, col.key) for col in
                        AlchemyExtras().get_pk_of(object_to_update.__class__)}
                    )
            ).set_next(
                ExistenceForeignKeysValidator(
                    self.session, on_body_validation_success
                )
            )
            body_validators.validate(context.request)
        except ValidationException as e:
            raise ValidationException(ValidationExceptionType.UPDATE_VALIDATION_EXCEPTION, HTTPStatus.BAD_REQUEST, e)

        assert object_to_update is not None

        return UpdateValidationResult(data_to_update, object_to_update)
