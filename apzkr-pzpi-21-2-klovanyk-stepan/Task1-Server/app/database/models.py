from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import String, CHAR, INT, ForeignKey, VARCHAR, UniqueConstraint, BIGINT, TEXT, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship


class CascadeForeignKey(ForeignKey):
    def __init__(self, *args, **kwargs):
        if kwargs.get('ondelete') is None:
            kwargs['ondelete'] = 'CASCADE'
        if kwargs.get('onupdate') is None:
            kwargs['onupdate'] = 'CASCADE'
        super().__init__(*args, **kwargs)


class Base(DeclarativeBase):
    pass


class User(Base, UserMixin):
    """
    Represents a user of the system.
    It can be either a customer or an employee.

    :var email: :class:`str` - [PK] Email
    :var nickname: :class:`str` - Nickname
    :var real_name: :class:`str` - Real name
    :var real_surname: :class:`str` - Real surname
    :var phone_number: :class:`str` - Phone number
    :var password_hash: :class:`str` - Password hash

    :var country_id: :class:`int` - [FK] :class:`Country` id

    :var country: :class:`Country` - Country as reference
    :var employee: :class:`Optional` of :class:`Employee` - Employee as reference
    :var bookings: :class:`list` of :class:`Booking` - Bookings as references

    """

    __tablename__ = "user"
    email: Mapped[str] = mapped_column(VARCHAR(320), primary_key=True)
    nickname: Mapped[str] = mapped_column(VARCHAR(35))
    real_name: Mapped[str] = mapped_column(CHAR(70))
    real_surname: Mapped[str] = mapped_column(CHAR(70))
    phone_number: Mapped[str] = mapped_column(CHAR(10))
    password_hash: Mapped[str] = mapped_column(VARCHAR(60))

    country_id: Mapped[int] = mapped_column(CascadeForeignKey('country.id'))

    country: Mapped['Country'] = relationship('Country', back_populates='users')
    employee: Mapped[Optional['Employee']] = relationship('Employee', back_populates='user')
    bookings: Mapped[list['Booking']] = relationship('Booking', back_populates='users', secondary='user_booking')

    def get_id(self):
        return self.email


class Employee(Base):
    """
    Represents an employee of the system.

    :var head_manager: :class:`bool` - Head manager
    :var booking_manager: :class:`bool` - Booking manager
    :var literature_manager: :class:`bool` - Literature manager
    :var literature_requests_manager: :class:`bool` - Literature requests manager
    :var iot_manager: :class:`bool` - Iot manager

    :var user_email: :class:`str` - [PK] [FK] :class:`User` email
    :var company_id: :class:`int` - [FK] :class:`Company` id

    :var user: :class:`User` - User as reference
    :var company: :class:`Company` - Company as reference
    :var registered_bookings: :class:`list` of :class:`Booking` - Registered bookings as references
    :var reviewed_requests: :class:`list` of :class:`LiteratureRequest` - Reviewed requests as references
    """

    __tablename__ = "employee"

    head_manager: Mapped[bool] = mapped_column(default=False)
    booking_manager: Mapped[bool] = mapped_column(default=False)
    literature_manager: Mapped[bool] = mapped_column(default=False)
    iot_manager: Mapped[bool] = mapped_column(default=False)

    user_email: Mapped[str] = mapped_column(CascadeForeignKey('user.email'), primary_key=True)
    establishment_id: Mapped[int] = mapped_column(CascadeForeignKey('establishment.id'))

    user: Mapped['User'] = relationship('User', back_populates='employee')
    establishment: Mapped['Establishment'] = relationship('Establishment', back_populates='employees')
    registered_bookings: Mapped[list['Booking']] = relationship('Booking', back_populates='registrator')
    edited_literatures: Mapped[list['Literature']] = relationship('Literature', back_populates='editor')


class Company(Base):
    """
    Represents a company of the system.

    :var id: :class:`int` - [PK] ID
    :var name: :class:`str` - Name
    :var global_access_company: :class:`bool` - Global access company

    :var employees: :class:`list` of :class:`Employee` - Employees as references
    :var establishments: :class:`list` of :class:`Establishment` - Establishments as references
    :var literature_requests: :class:`list` of :class:`LiteratureRequest` - Literature requests as references
    """
    __tablename__ = "company"
    id: Mapped[int] = mapped_column(INT, primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(255))
    global_access_company: Mapped[bool] = mapped_column()

    establishments: Mapped[list['Establishment']] = relationship('Establishment', back_populates='company')
    literatures: Mapped[list['Literature']] = relationship('Literature', back_populates='company')

class Establishment(Base):
    """
    Represents an establishment of the system.

    :var id: :class:`int` - [PK] ID
    :var address: :class:`str` - Address

    :var company_id: :class:`int` - [FK] :class:`Company` id
    :var country_id: :class:`int` - [FK] :class:`Country` id

    :var company: :class:`Company` - Company as reference
    :var country: :class:`Country` - Country as reference
    :var rooms: :class:`list` of :class:`Room` - Rooms as references
    """
    __tablename__ = "establishment"
    id: Mapped[int] = mapped_column(INT, primary_key=True)
    address: Mapped[str] = mapped_column(VARCHAR(255))

    company_id: Mapped[int] = mapped_column(CascadeForeignKey('company.id'))
    country_id: Mapped[int] = mapped_column(CascadeForeignKey('country.id'))

    company: Mapped['Company'] = relationship('Company', back_populates='establishments')
    country: Mapped['Country'] = relationship('Country', back_populates='establishments')
    rooms: Mapped[list['Room']] = relationship('Room', back_populates='establishment')
    employees: Mapped[list['Employee']] = relationship('Employee', back_populates='establishment')
    # bookings: Mapped[list['Booking']] = relationship('Booking', back_populates='establishment')


class Country(Base):
    """
    Represents a country of the system.

    :var id: :class:`int` - [PK] ID
    :var name: :class:`str` - Name
    :var charcode: :class:`str` - Charcode (example: UA, US, EN etc.)
    :var code: :class:`int` - Code

    :var users: :class:`list` of :class:`User` - Users as references
    :var establishments: :class:`list` of :class:`Establishment` - Establishments as references
    """
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(INT, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    charcode: Mapped[str] = mapped_column(CHAR(2))
    code: Mapped[int] = mapped_column(INT)

    users: Mapped[list['User']] = relationship('User', back_populates='country')
    establishments: Mapped[list['Establishment']] = relationship('Establishment', back_populates='country')


class Room(Base):
    """
    Represents a room of the system.

    :var id: :class:`int` - [PK] ID
    :var label: :class:`str` - Label

    :var establishment_id: :class:`int` - [FK] :class:`Establishment` id

    :var establishment: :class:`Establishment` - Establishment as reference
    :var light_devices: :class:`list` of :class:`LightDevice` - Light devices as references
    :var bookings: :class:`list` of :class:`Booking` - Bookings as references
    """
    __tablename__ = "room"
    __table_args__ = (UniqueConstraint('establishment_id', 'label', name='unique_room'),)

    id: Mapped[int] = mapped_column(INT, primary_key=True)
    label: Mapped[str] = mapped_column(VARCHAR(255))

    establishment_id: Mapped[int] = mapped_column(CascadeForeignKey('establishment.id'))

    establishment: Mapped['Establishment'] = relationship('Establishment', back_populates='rooms')
    light_devices: Mapped[list['LightDevice']] = relationship('LightDevice', back_populates='room')
    bookings: Mapped[list['Booking']] = relationship('Booking', back_populates='room')


class LightType(Base):
    """
    Represents a light type of the system.

    :var name: :class:`str` - [PK] Name

    :var light_devices: :class:`list` of :class:`LightDevice` - Light devices as references
    """
    __tablename__ = 'light_type'

    name: Mapped[str] = mapped_column(CHAR(20), primary_key=True)

    light_devices: Mapped[list['LightDevice']] = relationship('LightDevice', back_populates='light_type')
    page_configs: Mapped[list['LiteraturePageConfig']] = relationship('LiteraturePageConfig', back_populates='light_type')

class LightDevice(Base):
    """
    Represents a light device of the system.

    :var id: :class:`int` - [PK] ID
    :var port: :class:`int` - Port

    :var light_type_name: :class:`str` - [FK] :class:`LightType` name
    :var room_id: :class:`int` - [FK] :class:`Room` id

    :var light_type: :class:`LightType` - Light type as reference
    :var room: :class:`Room` - Room as reference
    """
    __tablename__ = "light_device"

    id: Mapped[int] = mapped_column(INT, primary_key=True)
    port: Mapped[int] = mapped_column(INT)
    host: Mapped[str] = mapped_column(VARCHAR(255))

    light_type_name: Mapped[Optional[str]] = mapped_column(CHAR(20), CascadeForeignKey('light_type.name'))
    room_id: Mapped[Optional[int]] = mapped_column(CascadeForeignKey('room.id'))
    details: Mapped[Optional[str]] = mapped_column(VARCHAR(255))

    light_type: Mapped[Optional['LightType']] = relationship('LightType', back_populates='light_devices')
    room: Mapped[Optional['Room']] = relationship('Room', back_populates='light_devices')


class LiteratureAuthor(Base):
    """
    Represents an author of the literature.

    :var literature_id: :class:`int` - [PK] [FK] :class:`Literature` id
    :var author_pseudonym: :class:`str` - [PK] [FK] :class:`Author` pseudonym
    """
    __tablename__ = "literature_author"

    literature_id: Mapped[int] = mapped_column(CascadeForeignKey('literature.id'), primary_key=True)
    author_id: Mapped[str] = mapped_column(CascadeForeignKey('author.id'), primary_key=True)


class LiteratureGenre(Base):
    """
    Represents a genre of the literature.

    :var literature_id: :class:`int` - [PK] [FK] :class:`Literature` id
    :var genre_name: :class:`str` - [PK] [FK] :class:`Genre` name
    """
    __tablename__ = "literature_genre"

    literature_id: Mapped[int] = mapped_column(CascadeForeignKey('literature.id'), primary_key=True)
    genre_name: Mapped[str] = mapped_column(CascadeForeignKey('genre.name'), primary_key=True)


class Author(Base):
    """
    Represents an author of the system.

    :var pseudonym: :class:`str` - [PK] Pseudonym
    :var name: :class:`Optional` of :class:`str` - Name
    :var surname: :class:`Optional` of :class:`str` - Surname

    :var literatures: :class:`list` of :class:`Literature` - Literatures as references
    """
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(INT, primary_key=True)
    pseudonym: Mapped[str] = mapped_column(VARCHAR(255))
    name: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
    surname: Mapped[Optional[str]] = mapped_column(VARCHAR(255))

    literatures: Mapped[list['Literature']] = relationship(
        'Literature', secondary='literature_author', back_populates='authors'
    )


class Genre(Base):
    """
    Represents a genre of the system.

    :var name: :class:`str` - [PK] Name

    :var literatures: :class:`list` of :class:`Literature` - Literatures as references
    """
    __tablename__ = "genre"

    name: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)

    literatures: Mapped[list['Literature']] = relationship(
        'Literature', secondary='literature_genre', back_populates='genres'
    )


class LiteratureType(Base):
    """
    Represents a type of the literature.

    :var name: :class:`str` - [PK] Name

    :var literatures: :class:`list` of :class:`Literature` - Literatures as references
    """
    __tablename__ = "literature_type"

    name: Mapped[str] = mapped_column(VARCHAR(255), primary_key=True)

    literatures: Mapped[list['Literature']] = relationship(
        'Literature', back_populates='type'
    )


class Literature(Base):
    """
    Represents a literature of the system.

    :var id: :class:`int` - [PK] ID
    :var name: :class:`str` - Name
    :var description: :class:`str` - Description
    :var pages: :class:`int` - Pages
    :var min_age: :class:`Optional` of :class:`int` - Min age
    :var pdf_PATH: :class:`Optional` of :class:`str` - Pdf path
    :var thumbnail_PATH: :class:`Optional` of :class:`str` - Thumbnail path
    :var editor_email: :class:`Optional` of :class:`str` - Editor email

    :var type_name: :class:`str` - [FK] :class:`LiteratureType` name

    :var type: :class:`LiteratureType` - LiteratureType as reference
    :var authors: :class:`list` of :class:`Author` - Authors as references
    :var genres: :class:`list` of :class:`Genre` - Genres as references
    """
    __tablename__ = "literature"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(255))
    description: Mapped[str] = mapped_column(TEXT)
    pages: Mapped[Optional[int]] = mapped_column(INT)
    min_age: Mapped[Optional[int]] = mapped_column(INT)
    pdf_PATH: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
    thumbnail_PATH: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
    editor_email: Mapped[Optional[str]] = mapped_column(ForeignKey('employee.user_email', ondelete='SET NULL'))
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey('company.id', ondelete='SET NULL'))

    company: Mapped['Company'] = relationship('Company', back_populates='literatures')

    type_name: Mapped[str] = mapped_column(CascadeForeignKey('literature_type.name'))

    type: Mapped['LiteratureType'] = relationship('LiteratureType', back_populates='literatures')
    authors: Mapped[list['Author']] = relationship(
        'Author', secondary='literature_author', back_populates='literatures'
    )
    genres: Mapped[list['Genre']] = relationship(
        'Genre', secondary='literature_genre', back_populates='literatures'
    )
    page_configs: Mapped[list['LiteraturePageConfig']] = relationship(
        'LiteraturePageConfig', back_populates='literature'
    )
    editor: Mapped['Employee'] = relationship('Employee', back_populates='edited_literatures')

    def get_unique_folder_path(self) -> str:
        return f"Literatures/{self.id}"


class Booking(Base):
    """
    Represents a booking of the system.

    :var id: :class:`int` - [PK] ID
    :var registration_time: :class:`datetime` - Registration time
    :var expiration_time: :class:`datetime` - Expiration time

    :var registrator_email: :class:`str` - [FK] :class:`Employee` email
    :var room_id: :class:`int` - [FK] :class:`Room` id

    :var registrator: :class:`Employee` - Employee as reference
    :var room: :class:`Room` - Room as reference
    :var users: :class:`list` of :class:`User` - Users as references
    """
    __tablename__ = "booking"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    registration_time: Mapped[datetime] = mapped_column(DateTime)
    expiration_time: Mapped[datetime] = mapped_column(DateTime)

    registrator_email: Mapped[str] = mapped_column(CascadeForeignKey('employee.user_email'))
    room_id: Mapped[int] = mapped_column(CascadeForeignKey('room.id'))
    # establishment_id: Mapped[int] = mapped_column(CascadeForeignKey('establishment.id'))

    registrator: Mapped['Employee'] = relationship('Employee', back_populates='registered_bookings')
    room: Mapped['Room'] = relationship('Room', back_populates='bookings')
    users: Mapped[list['User']] = relationship('User', back_populates='bookings', secondary='user_booking')

    # establishment: Mapped['Establishment'] = relationship('Establishment', back_populates='bookings')

class UserBooking(Base):
    """
    Represents a user booking of the system.

    :var user_email: :class:`str` - [PK] [FK] :class:`User` email
    :var booking_id: :class:`int` - [PK] [FK] :class:`Booking` id
    """
    __tablename__ = "user_booking"

    user_email: Mapped[str] = mapped_column(CascadeForeignKey('user.email'), primary_key=True)
    booking_id: Mapped[int] = mapped_column(CascadeForeignKey('booking.id'), primary_key=True)


class LiteraturePageConfig(Base):
    """
    Represents a page configuration of the literature.

    :var id: :class:`int` - [PK] ID
    :var literature_id: :class:`int` - [FK] :class:`Literature` id
    :var page_number: :class:`int` - Page number
    :var configuration: :class:`dict` - Configuration

    :var literature: :class:`Literature` - Literature as reference
    """
    __tablename__ = "literature_page_config"

    __table_args__ = (UniqueConstraint('literature_id', 'page_number', 'light_type_name'),)

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    literature_id: Mapped[int] = mapped_column(CascadeForeignKey('literature.id'))
    page_number: Mapped[int] = mapped_column(INT)
    light_type_name: Mapped[str] = mapped_column(CascadeForeignKey('light_type.name'))
    configuration = mapped_column(JSON)

    literature: Mapped['Literature'] = relationship('Literature', back_populates='page_configs')

    light_type: Mapped['LightType'] = relationship('LightType', back_populates='page_configs')

class DeviceConfig:
    """
    Configuration used for the device.

    :var color: :class:`int` - Color
    :var color_alter: :class:`int` - Color alter
    :var color_alter_ms_delta: :class:`int` - Color alter ms delta
    """

    class DeviceType(StrEnum):
        SKY = "Sky"
        SUN = "Sun"
        MOON = "Moon"
        ENV = "Environment"
        GROUND = "Ground"

    def __init__(
            self, color: int, color_alter: int = None,
            color_alter_ms_delta: int = None
    ):
        self.color = color
        self.color_alter = color_alter
        self.color_alter_ms_delta = color_alter_ms_delta

    def to_dict(self):
        return self.__dict__

    def serialize(self):
        return json.dumps(self.to_dict())

    @classmethod
    def deserialize(cls, data):
        return cls.from_dict(json.loads(data))

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
