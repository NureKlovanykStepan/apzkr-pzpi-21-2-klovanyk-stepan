from __future__ import annotations

import functools
from dataclasses import dataclass
from enum import IntFlag, auto
from http import HTTPStatus

from app import Globals
from app.database.models import User
from app.services.validators.base import ValidationException, ValidationExceptionType


@dataclass
class RequiredPermissionsFlag(IntFlag):
    HEAD_MANAGER = auto()
    BOOKING_MANAGER = auto()
    LITERATURE_MANAGER = auto()
    IOT_MANAGER = auto()

    @classmethod
    @property
    def ALL(cls) -> RequiredPermissionsFlag:
        return functools.reduce(lambda a, b: a | b, cls.__members__.values())

    @classmethod
    @property
    def NONE(cls):
        return cls(0)

    @property
    def as_list(self):
        return [item for item in self]


def permissions_of_employee_required(
        user: User, required_permissions: RequiredPermissionsFlag = RequiredPermissionsFlag.ALL
):
    """
    Decorator for employee access.
    Requires wrapped function to take 'requestor_employee' argument of type :class:`Employee`.
    :param user:
    :param required_permissions:
    :return:
    """

    def Decorator(func):
        @functools.wraps(func)
        def Wrapper(*args, **kwargs):
            current_user = Globals().db.session().get(User, user.get_id())
            if not current_user.employee:
                raise ValidationException(ValidationExceptionType.NOT_EMPLOYEE, HTTPStatus.FORBIDDEN)

            employee = current_user.employee
            required_permissions_dict = {flag.name: flag.value for flag in required_permissions.as_list}
            for permission, is_required in required_permissions_dict.items():
                if not is_required:
                    continue
                if not getattr(employee, permission.lower()):
                    raise ValidationException(
                        ValidationExceptionType.NOT_ENOUGH_PERMISSIONS, HTTPStatus.FORBIDDEN
                    )

            # return func(*args, requestor_employee=employee, **kwargs)
            return func(*args, **kwargs)

        return Wrapper

    return Decorator
