import dataclasses
import uuid
from http import HTTPStatus

from flask_sqlalchemy.session import Session
from icecream import ic
from sqlalchemy import and_

from app import SingletonMeta
from app.database.models import Establishment, Room, LightDevice
from app.services.validators.base import ValidationException, ValidationExceptionType
from app.utils.extra import SecondaryConfig


class DeviceRegistrationManager(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.current_gates: dict[int, tuple[str, int | None]] = {}

    @dataclasses.dataclass
    class RegistrationData:
        establishment_id: int
        room_id: int | None = None

    def get_unique_code(self):
        return uuid.uuid4().hex

    def open_gate(self, session: Session, establishment_id: int) -> str:
        self.validate_establishment_existence(session, establishment_id)
        self.current_gates[establishment_id] = (code := self.get_unique_code(), None)
        return code

    def close_gate(self, establishment_id: int):
        if establishment_id not in self.current_gates:
            return
        self.current_gates.pop(establishment_id)

    def validate_establishment_existence(self, session: Session, establishment_id: int):
        if not session.get(Establishment, establishment_id):
            raise ValidationException(
                ValidationExceptionType.PK_OBJECT_NOT_FOUND, HTTPStatus.NOT_FOUND,
                f'Establishment with id {establishment_id} not found'
            )

    def validate_room_existence(self, session: Session, room_id: int):
        if not session.get(Room, room_id):
            raise ValidationException(
                ValidationExceptionType.PK_OBJECT_NOT_FOUND, HTTPStatus.NOT_FOUND, f'Room with id {room_id} not found'
            )

    def validate_gate_existence(self, establishment_id: int):
        if establishment_id not in self.current_gates:
            raise ValidationException(
                ValidationExceptionType.NO_GATE,
                HTTPStatus.NOT_FOUND,
                f'No gate opened on establishment {establishment_id}'
            )

    def validate_room_belongs_to_establishment(self, session: Session, room_id: int, establishment_id: int):
        if not (rid := session.get(Room, room_id).establishment_id) == establishment_id:
            ic(rid, establishment_id)
            raise ValidationException(
                ValidationExceptionType.ROOM_NOT_BELONG_TO_ESTABLISHMENT, HTTPStatus.BAD_REQUEST,
                f'Room {room_id} not belongs to establishment {establishment_id}'
            )

    def get_establishment_by_code(self, code: str):
        for establishment, data in self.current_gates.items():
            if data[0] == code:
                return establishment, data[0], data[1]
        raise ValidationException(
            ValidationExceptionType.NO_GATE, HTTPStatus.NOT_FOUND, f'No gate opened on code {code}'
        )

    def define_room(self, session: Session, establishment_id: int, room_id: int):
        self.validate_establishment_existence(session, establishment_id)
        self.validate_room_existence(session, room_id)
        self.validate_gate_existence(establishment_id)
        self.validate_room_belongs_to_establishment(session, room_id, establishment_id)
        self.current_gates[establishment_id] = (self.current_gates[establishment_id][0], room_id)
        return "OK", 200

    def register_device(self, session: Session, code: str, host: str):
        establishment_id, code, room_id = self.get_establishment_by_code(code)
        self.validate_establishment_existence(session, establishment_id)
        self.validate_room_existence(session, room_id)

        port = self.get_available_port(session, establishment_id)
        session.add(
            LightDevice(
                port=port, room_id=room_id, host=host
            )
        )
        session.commit()
        self.current_gates[establishment_id] = (new_code := self.get_unique_code(), room_id)
        return port, new_code

    def get_available_port(self, session: Session, establishment_id: int) -> int:
        available_range = SecondaryConfig().ESTABLISHMENT_PORT_RANGE
        all_devices_for_establishment = session.query(LightDevice).join(
            Room, and_(Room.id == LightDevice.room_id, Room.establishment_id == establishment_id)
        ).all()
        ic(all_devices_for_establishment, establishment_id)
        all_ports = [device.port for device in all_devices_for_establishment]

        for port in range(available_range[0], available_range[1] + 1):
            if port not in all_ports:
                return port
