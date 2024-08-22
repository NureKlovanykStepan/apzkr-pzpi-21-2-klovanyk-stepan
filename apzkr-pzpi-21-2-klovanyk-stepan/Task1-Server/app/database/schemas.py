from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, fields

from .models import *


class BaseSchema(SQLAlchemyAutoSchema):
    pass


class UserSchema(BaseSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True

    country = fields.Nested(
        lambda: CountrySchema, many=False, exclude=['users']
    )
    employee = fields.Nested(
        lambda: EmployeeSchema, many=False, exclude=['user']
    )
    bookings = fields.Nested(
        lambda: BookingSchema, many=True, exclude=['users']
    )


class EmployeeSchema(BaseSchema):
    class Meta:
        model = Employee
        load_instance = True
        include_fk = True

    user = fields.Nested(
        lambda: UserSchema, many=False, exclude=['employee']
    )
    establishment = fields.Nested(
        lambda: EstablishmentSchema, many=False, exclude=['employees']
    )
    registered_bookings = fields.Nested(
        lambda: BookingSchema, many=True, exclude=['registrator']
    )


class CompanySchema(BaseSchema):
    class Meta:
        model = Company
        load_instance = True
        include_fk = True

    establishments = fields.Nested(
        lambda: EstablishmentSchema, many=True, exclude=['company']
    )


class EstablishmentSchema(BaseSchema):
    class Meta:
        model = Establishment
        load_instance = True
        include_fk = True

    company = fields.Nested(
        lambda: CompanySchema, many=False, exclude=['establishments']
    )
    country = fields.Nested(
        lambda: CountrySchema, many=False, exclude=['establishments']
    )
    rooms = fields.Nested(
        lambda: RoomSchema, many=True, exclude=['establishment']
    )
    employees = fields.Nested(
        lambda: EmployeeSchema, many=True, exclude=['establishment']
    )


class CountrySchema(BaseSchema):
    class Meta:
        model = Country
        load_instance = True
        include_fk = True

    users = fields.Nested(
        lambda: UserSchema, many=True, exclude=['country']
    )
    establishments = fields.Nested(
        lambda: EstablishmentSchema, many=True, exclude=['country']
    )


class RoomSchema(BaseSchema):
    class Meta:
        model = Room
        load_instance = True
        include_fk = True

    establishment = fields.Nested(
        lambda: EstablishmentSchema, many=False, exclude=['rooms']
    )
    light_devices = fields.Nested(
        lambda: LightDeviceSchema, many=True, exclude=['room']
    )
    bookings = fields.Nested(
        lambda: BookingSchema, many=True, exclude=['room']
    )


class LightTypeSchema(BaseSchema):
    class Meta:
        model = LightType
        load_instance = True
        include_fk = True

    light_devices = fields.Nested(
        lambda: LightDeviceSchema, many=True, exclude=['light_type']
    )


class LightDeviceSchema(BaseSchema):
    class Meta:
        model = LightDevice
        load_instance = True
        include_fk = True

    room = fields.Nested(
        lambda: RoomSchema, many=False, exclude=['light_devices']
    )
    light_type = fields.Nested(
        lambda: LightTypeSchema, many=False, exclude=['light_devices']
    )


class LiteratureAuthorSchema(BaseSchema):
    class Meta:
        model = LiteratureAuthor
        load_instance = True
        include_fk = True


class LiteratureGenreSchema(BaseSchema):
    class Meta:
        model = LiteratureGenre
        load_instance = True
        include_fk = True


class AuthorSchema(BaseSchema):
    class Meta:
        model = Author
        load_instance = True
        include_fk = True

    literatures = fields.Nested(
        lambda: LiteratureSchema, many=True, exclude=['authors']
    )


class GenreSchema(BaseSchema):
    class Meta:
        model = Genre
        load_instance = True
        include_fk = True

    literatures = fields.Nested(
        lambda: LiteratureSchema, many=True, exclude=['genres']
    )


class LiteratureTypeSchema(BaseSchema):
    class Meta:
        model = LiteratureType
        load_instance = True
        include_fk = True

    literatures = fields.Nested(
        lambda: LiteratureSchema, many=True, exclude=['type']
    )


class LiteratureSchema(BaseSchema):
    class Meta:
        model = Literature
        load_instance = True
        include_fk = True

    type = fields.Nested(
        lambda: LiteratureTypeSchema, many=False, exclude=['literatures']
    )
    authors = fields.Nested(
        lambda: AuthorSchema, many=True, exclude=['literatures']
    )
    genres = fields.Nested(
        lambda: GenreSchema, many=True, exclude=['literatures']
    )
    page_configs = fields.Nested(
        lambda: LiteraturePageConfigSchema, many=True, exclude=['literature']
    )


class BookingSchema(BaseSchema):
    class Meta:
        model = Booking
        load_instance = True
        include_fk = True

    registrator = fields.Nested(
        lambda: EmployeeSchema, many=False, exclude=['registered_bookings']
    )
    room = fields.Nested(
        lambda: RoomSchema, many=False, exclude=['bookings']
    )
    users = fields.Nested(
        lambda: UserSchema, many=True, exclude=['bookings']
    )


class UserBookingSchema(BaseSchema):
    class Meta:
        model = UserBooking
        load_instance = True
        include_fk = True


class LiteraturePageConfigSchema(BaseSchema):
    class Meta:
        model = LiteraturePageConfig
        load_instance = True
        include_fk = True

    literature = fields.Nested(
        lambda: LiteratureSchema, many=False, exclude=['page_configs']
    )


if __name__ == "__main__":
    pass
