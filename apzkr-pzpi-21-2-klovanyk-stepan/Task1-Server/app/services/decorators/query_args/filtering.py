from functools import wraps

from flask import Request

from app.database.models import Base
from app.services.processors.filtering import RequestQueryArgsResolver


def filtering_args(request: Request, for_type: type[Base]):
    def Decorator(func):
        @wraps(func)
        def Wrapper(*args, **kwargs):
            return func(
                *args, filtering_query_mod=RequestQueryArgsResolver(request, for_type).process_args(), **kwargs
            )

        return Wrapper

    return Decorator
