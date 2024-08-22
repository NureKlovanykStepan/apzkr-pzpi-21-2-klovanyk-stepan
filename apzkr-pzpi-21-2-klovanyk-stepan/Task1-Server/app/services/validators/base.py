from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional, Callable

from marshmallow import ValidationError
from marshmallow.validate import Email as EmailValidator
from sqlalchemy.orm import Session

from app.utils.base import MessageType


class ValidationExceptionType(MessageType):
    # General validators errors
    INVALID_QUALITY = 'Quality of provided data is invalid'
    RELATIVE_AND_ABSOLUTE_CONFLICT = 'A conflict of providing both relative and absolute data'
    INVALID_JSON = 'Provided data was invalid or not a JSON'
    TYPES_CONVERSION_EXCEPTION = 'Types conversion exception'
    RAW_JSON_CONVERSION_EXCEPTION = 'Raw JSON conversion exception'
    MARSHMALLOW_VALIDATION_EXCEPTION = 'Marshmallow validators exception'

    # Request-related errors
    REQUEST_MISSING_FILE = 'Request missing file'
    INVALID_CONTENT_TYPE = 'Invalid content type'
    REQUEST_BODY_MISSING_PK = 'Missing primary key in request body'
    REQUEST_BODY_MISSING_FIELD = 'Missing field in request body'
    REQUEST_BODY_UNKNOWN_FIELD = 'Unknown field in request body'

    # Database and object-related errors
    RESOURCE_NOT_FOUND = 'Resource not found'
    PARENT_OBJECT_NOT_FOUND = 'Parent object not found'
    PK_OBJECT_ALREADY_EXISTS = 'Object with provided primary key already exists'
    PK_OBJECT_NOT_FOUND = 'Object with provided primary key not found'
    PK_FIELDS_COUNT_MISMATCH = 'PK fields count mismatch'
    DIRECT_RELATIONSHIPS_UNSUPPORTED = 'Direct relationships are not supported'

    # Specific domain-related errors
    NO_BOOKINGS_AVAILABLE = 'No bookings available'
    ROOM_NOT_BELONG_TO_ESTABLISHMENT = 'Room does not belong to establishment'
    NO_ROOM_FOR_GATE = 'No room for this gate'
    NO_GATE = 'No gate opened on this key'
    LOCKED_RESOURCE = 'Resource cannot be accessed'
    BOOKINGS_MISSING = 'Bookings missing'
    EMPLOYEE_COMPANY_MISMATCH = 'Employee and company mismatch'

    # Authentication and authorization errors
    NO_AUTH = 'No Auth Method have been provided'
    UNSUPPORTED_AUTH = 'Unsupported Auth Method'
    USER_NOT_FOUND = 'User Not Found'
    INVALID_PASSWORD = 'Invalid Password'
    NOT_EMPLOYEE = 'Only employees can perform this action'
    NOT_ENOUGH_PERMISSIONS = 'You don\'t have enough permissions to perform this action'

    # Input validators errors
    INVALID_EMAIL = 'Invalid Email'
    INVALID_PHONE_NUMBER_LENGTH = 'Invalid phone number length'

    # CRUD operation-specific errors
    DELETE_VALIDATION_EXCEPTION = 'Delete validators exception'
    UPDATE_VALIDATION_EXCEPTION = 'Update validators exception'
    READ_VALIDATION_EXCEPTION = 'Read validators exception'
    CREATE_VALIDATION_EXCEPTION = 'Create validators exception'



class BaseFormattedRequestException(Exception, ABC):
    @abstractmethod
    def message_dict(self) -> dict[str, any]:
        raise NotImplementedError

    def __init__(self, response_type: MessageType, http_status_code: int, message=None):
        self.response_type = response_type
        self.http_status_code = http_status_code
        self.message = message

        self.details = self.message_dict()

        super().__init__('\n'.join(f'{key}: {value}' for key, value in self.details.items()))


class ValidationException(BaseFormattedRequestException):
    def message_dict(self) -> dict[str, any]:
        details = {
            'ERROR_TYPE': self.response_type.name, 'ERROR_MESSAGE': self.response_type,
        }
        if self.message is not None:
            details['ERROR_DETAILS'] = '\n'+'\n'.join(
                f'>> {message_line}' for message_line in str(self.message).split('\n')
            )
        return details


@dataclass
class BaseValidator[Accepts, Provides](ABC):
    on_success_callback: Optional[Callable[[Provides], None]] = None
    next_validator: Optional[BaseValidator[Provides, any]] = None

    @abstractmethod
    def _validation_body(self, context: Accepts) -> Provides:
        pass

    def validate(self, context: Accepts):
        provides = self._validation_body(context)
        if self.on_success_callback:
            self.on_success_callback(provides)
        if self.next_validator:
            self.next_validator.validate(provides)

    def set_next(self, next_validator: BaseValidator[Provides, any]):
        self.next_validator = next_validator
        return next_validator


class BaseSessionAffectedValidator[Accepts, Provides](BaseValidator[Accepts, Provides], ABC):
    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

class BasicEmailValidator(BaseValidator[str, str]):
    def _validation_body(self, context: str) -> str:
        try:
            EmailValidator()(context)
        except ValidationError as e:
            raise ValidationException(
                ValidationExceptionType.INVALID_EMAIL, HTTPStatus.BAD_REQUEST, e.normalized_messages()
            )
        return context


class BasicPhoneNumberLengthValidator(BaseValidator[str, str]):
    def _validation_body(self, context: str) -> str:
        if not len(context) == 10:
            raise ValidationException(
                ValidationExceptionType.INVALID_PHONE_NUMBER_LENGTH, HTTPStatus.BAD_REQUEST
            )
        return context


class BaseDataConverter(ABC):
    def __init__(self, unconverted: dict):
        self.unconverted = unconverted

    @abstractmethod
    def convert(self) -> dict[str, any]:
        raise NotImplementedError

    @abstractmethod
    def get_conversion_fields_mapping(self) -> dict[str, str]:
        """
        The mapping represents relaton between input fields and produced fields.
        :return:
        """
        raise NotImplementedError
