from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional

from flask import Request

from app import Globals
from app.database.models import User
from app.services.validators.base import ValidationExceptionType, ValidationException, BasicEmailValidator, \
    BaseValidator


@dataclass
class AuthRequest:
    email: str
    password: str


@dataclass
class AuthDefinedUser:
    user: User
    password: str


class AuthMethodValidator(BaseValidator[Request, AuthRequest]):
    def _validation_body(self, context: Request) -> AuthRequest:
        if not context.authorization:
            raise ValidationException(ValidationExceptionType.NO_AUTH, HTTPStatus.UNAUTHORIZED)
        if not context.authorization.type == 'basic':
            raise ValidationException(ValidationExceptionType.UNSUPPORTED_AUTH, HTTPStatus.UNAUTHORIZED)
        return AuthRequest(context.authorization.username, context.authorization.password)


class AuthEmailValidator(BaseValidator[AuthRequest, AuthRequest]):
    def _validation_body(self, context: AuthRequest) -> AuthRequest:
        BasicEmailValidator().validate(context.email)
        return context


class AuthUserValidator(BaseValidator[AuthRequest, AuthDefinedUser]):
    def _validation_body(self, context: AuthRequest) -> AuthDefinedUser:
        with Globals().db.session() as session:
            user = session.get(User, context.email)
            if not user:
                raise ValidationException(ValidationExceptionType.USER_NOT_FOUND, HTTPStatus.NOT_FOUND)
        return AuthDefinedUser(user, context.password)


class AuthPasswordValidator(BaseValidator[AuthDefinedUser, AuthDefinedUser]):
    def _validation_body(self, context: AuthDefinedUser) -> AuthDefinedUser:
        if not Globals().bcrypt.check_password_hash(context.user.password_hash, context.password):
            raise ValidationException(ValidationExceptionType.INVALID_PASSWORD, HTTPStatus.UNAUTHORIZED)
        return context


class AuthGeneralValidator(BaseValidator[Request, Optional[User]]):
    def _validation_body(self, context: Request) -> Optional[User]:
        user = None

        def on_success(provides: AuthDefinedUser):
            nonlocal user
            user = provides.user

        validator = AuthMethodValidator()
        validator.set_next(AuthEmailValidator()).set_next(AuthUserValidator()).set_next(
            AuthPasswordValidator(on_success)
        )
        validator.validate(context)

        return user
