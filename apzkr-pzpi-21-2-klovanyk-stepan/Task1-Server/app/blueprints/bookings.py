import datetime
from typing import Callable, cast

from flask import Blueprint, request
from flask_login import login_required, current_user
from sqlalchemy.orm import Query

from app import Globals
from app.database.models import Booking, User
from app.secret_config import SecretConfig
from app.utils.extra import BlueprintsStorage
from app.services.creators.builders.routes import RequestModifiers, RoutesBuilder
from app.services.creators.factories.body import RequestBodyFactory
from app.services.creators.factories.body_details import BodyFactoryDetailsFactory
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm
from app.services.validators.base import ValidationException

bookings = Blueprint('bookings', __name__, url_prefix=SecretConfig().API_PREFIX + '/bookings')
BlueprintsStorage().register(bookings)
used_base_type = Booking


@bookings.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@bookings.post('/')
@login_required
@permissions_of_employee_required(current_user, Perm.BOOKING_MANAGER)
def create(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_create_body()()


@bookings.get('/')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.BOOKING_MANAGER)
@filtering_args(request, used_base_type)
def read_all(
        serialization_modifiers: RequestArgsParser.Result,
        filtering_query_mod: Callable[[Query], Query], **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
            serialization_modifiers,
            filtering_query_mod
        )()


@bookings.get('/forRoom/<room_id>')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.BOOKING_MANAGER)
def read_by_room(
        room_id: int,
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
            serialization_modifiers, lambda query: query.where(Booking.room_id == room_id)
        )()


@bookings.get('/<id>')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.BOOKING_MANAGER)
def read_one(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(serialization_modifiers)()


@bookings.put('/<id>')
@login_required
@permissions_of_employee_required(current_user, Perm.BOOKING_MANAGER)
def update(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_update_body()()


@bookings.delete('/<id>')
@login_required
@permissions_of_employee_required(current_user, Perm.BOOKING_MANAGER)
def delete(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_delete_body()()


@bookings.get('/me')
@login_required
@serialization_args(request, used_base_type)
def read_self(serialization_modifiers: RequestArgsParser.Result, **kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
            serialization_modifiers,
            BookingsQueryHelper().availableActiveBookings()
        )()


addition = (RoutesBuilder(bookings, used_base_type)
.route_Reset().route_AppendCategory('my')
.modifiers_Use(RequestModifiers.SERIALIZATION | RequestModifiers.FILTERING)
.buildRequest_onBodyFactory(
    lambda adf: cast(BodyFactoryDetailsFactory, adf).READ_MANY(
        lambda query, request_args: BookingsQueryHelper().availableActiveBookings()(query)
    )
))


class BookingsQueryHelper:
    def __init__(self, requestor_provider: Callable[[], User] = lambda: current_user):
        self.requestor_provider = requestor_provider

    def availableBookings(self):
        def modifier(query: Query):
            requestor = self.requestor_provider()
            return query.where(Booking.users.contains(requestor))

        return modifier

    def availableActiveBookings(self):
        available_bookings = self.availableBookings()

        def modifier(query: Query):
            return available_bookings(query).where(
                Booking.registration_time <= (now := datetime.datetime.now(datetime.UTC)),
                Booking.expiration_time >= now
            )

        return modifier
