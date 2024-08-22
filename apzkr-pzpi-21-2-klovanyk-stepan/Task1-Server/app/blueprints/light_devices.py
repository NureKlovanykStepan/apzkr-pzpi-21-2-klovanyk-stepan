from http import HTTPStatus
from io import BytesIO
from typing import Callable, cast

from flask import Blueprint, request, send_file
from flask_login import login_required, current_user
from sqlalchemy.orm import Query

from app import Globals
from app.blueprints.bookings import BookingsQueryHelper
from app.database.models import LightDevice, Room, Booking
from app.secret_config import SecretConfig
from app.services.processors.device_registering import DeviceRegistrationManager
from app.utils.extra import BlueprintsStorage, SecondaryConfig
from app.services.creators.builders.routes import RoutesBuilder, RequestModifiers
from app.services.creators.factories.body import RequestBodyFactory
from app.services.creators.factories.body_details import BodyFactoryDetailsFactory, BodyFactoryDetails
from app.services.decorators.query_args.filtering import filtering_args
from app.services.decorators.query_args.serialization import RequestArgsParser, serialization_args
from app.services.decorators.general.permissions import permissions_of_employee_required, \
    RequiredPermissionsFlag as Perm
from app.services.validators.base import ValidationException, ValidationExceptionType

light_devices = Blueprint('light_devices', __name__, url_prefix=SecretConfig().API_PREFIX + '/light_devices')
BlueprintsStorage().register(light_devices)
used_base_type = LightDevice


@light_devices.errorhandler(ValidationException)
def validation_exception_handler(validation_exception: ValidationException):
    return str(validation_exception), validation_exception.http_status_code


@light_devices.post('/')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def create(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_create_body()()


@light_devices.get('/')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
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


@light_devices.get('/forRoom/<room_id>')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def read_by_room(
        room_id: int, serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_many_body(
            serialization_modifiers, lambda query: query.where(LightDevice.room_id == room_id)
        )()


@light_devices.get('/<id>')
@login_required
@serialization_args(request, used_base_type)
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def read_one(
        serialization_modifiers: RequestArgsParser.Result, **kwargs
):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_read_single_body(serialization_modifiers)()


@light_devices.put('/<id>')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def update(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_update_body()()


@light_devices.delete('/<id>')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def delete(**kwargs):
    with Globals().db.session() as session:
        return RequestBodyFactory(session, used_base_type, request).get_crud_delete_body()()


@light_devices.get('iot_registration_service/<establishment_id>')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def get_gate(establishment_id: int, **kwargs):
    if not (gate_data := DeviceRegistrationManager().current_gates.get(int(establishment_id))):
        raise ValidationException(
            ValidationExceptionType.NO_GATE, HTTPStatus.NOT_FOUND, f'No gate opened on establishment {establishment_id}'
        )
    return {'room_id': gate_data[1], 'code': gate_data[0]}


@light_devices.post('iot_registration_service/<establishment_id>')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def open_gate(establishment_id: int, **kwargs):
    with Globals().db.session() as session:
        return DeviceRegistrationManager().open_gate(session, int(establishment_id))


@light_devices.get('iot_registration_service/<establishment_id>/iot_file')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def get_iot_registration_file(establishment_id: int, **kwargs):
    with Globals().db.session() as session:
        if not (gate_data := DeviceRegistrationManager().current_gates.get(int(establishment_id))):
            raise ValidationException(
                ValidationExceptionType.NO_GATE,
                HTTPStatus.NOT_FOUND,
                f'No gate opened on establishment {establishment_id}'
            )
        return send_file(
            BytesIO(gate_data[0].encode()),
            mimetype='text/plain',
            as_attachment=True,
            download_name=SecondaryConfig().IOT_REG_FILE_NAME
        )


@light_devices.delete('iot_registration_service/<establishment_id>')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def close_gate(establishment_id: int, **kwargs):
    DeviceRegistrationManager().close_gate(int(establishment_id))
    return "OK", 200


@light_devices.post('iot_registration_service/<establishment_id>/room/<room_id>')
@login_required
@permissions_of_employee_required(current_user, Perm.IOT_MANAGER)
def define_room(establishment_id: int, room_id: int, **kwargs):
    with Globals().db.session() as session:
        return DeviceRegistrationManager().define_room(session, int(establishment_id), int(room_id))


@light_devices.post('/iot_registration_service/register/<code>/<host>')
def register_device(code: str, host: str, **kwargs):
    with Globals().db.session() as session:
        data = DeviceRegistrationManager().register_device(session, code, host)
        return {
            'port': data[0],
            'code': data[1]
        }


def using_details_factory(bfdf: BodyFactoryDetailsFactory) -> BodyFactoryDetails:
    def query_mod(query: Query, request_data: dict[str, any]) -> Query:
        session = request_data['session']
        availableBookings = (BookingsQueryHelper(lambda: current_user).availableActiveBookings()(session.query(Booking))
                             .join(q := query.subquery(), q.c.room_id == Booking.room_id))
        if not (firstAvailable := cast(Booking, availableBookings.first())):
            raise ValidationException(ValidationExceptionType.NO_BOOKINGS_AVAILABLE, HTTPStatus.FORBIDDEN)
        
        devicesQuery = session.query(LightDevice).join(Room).where(Room.id == firstAvailable.room_id)
        return devicesQuery

    return bfdf.READ_MANY(query_mod)


extended = (RoutesBuilder(light_devices, used_base_type)
            .useDefault_ValidationExceptionHandler()
            .modifiers_Use(RequestModifiers.LOGIN)
            .modifiers_Use(RequestModifiers.SERIALIZATION | RequestModifiers.FILTERING)
            .route_Reset().route_AppendCategory('first_accessible')
            .buildRequest_onBodyFactory(using_details_factory))
