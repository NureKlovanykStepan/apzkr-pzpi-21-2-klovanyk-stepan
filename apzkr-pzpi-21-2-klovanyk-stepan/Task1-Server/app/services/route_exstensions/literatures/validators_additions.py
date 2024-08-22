from http import HTTPStatus

from flask import request
from icecream import ic
from sqlalchemy import or_, select, distinct
from sqlalchemy.orm import Session, Query

from app.blueprints.bookings import BookingsQueryHelper
from app.database.models import User, Literature, Employee, Booking, Company, Establishment, Room, Genre
from app.services.processors.tools import RequestHelper
from app.services.validators.base import ValidationException, ValidationExceptionType
from app.utils.extra import ValidatorsData


def validate_IsLiteratureCanBeFullyRead(
        user: User,
        literature: Literature,
        request_data: dict[str, any],
        session: Session
) -> ValidationException | None:
    def validateCase_User(bound_user_: User, session_: Session) -> ValidationException | None:
        if not (availableLiteratures_ForUser(session_.query(Literature), bound_user_, session_)
                .where(Literature.id == literature.id)
                .first()):
            return ValidationException(
                ValidationExceptionType.NO_BOOKINGS_AVAILABLE, HTTPStatus.FORBIDDEN
            )

    def validateCase_Employee(employee_: Employee, session_: Session) -> ValidationException | None:
        if employee_.establishment.company.global_access_company:
            return None

        if not (availableLiteratures_ForEmployeeToRead(session_.query(Literature), employee_)
                .where(Literature.id == literature.id)
                .first()):
            return ValidationException(
                ValidationExceptionType.NO_BOOKINGS_AVAILABLE, HTTPStatus.FORBIDDEN
            )

    bound_user = RequestHelper.get_current_bound_user(session, user)

    if employee := bound_user.employee:
        return validateCase_Employee(employee, session)
    else:
        return validateCase_User(bound_user, session)


def validate_IsLiteratureCanBeEdited(
        user: User,
        literature: Literature,
        extra: dict[str, any],
        session: Session
) -> ValidationException | None:
    bound_user = RequestHelper.get_current_bound_user(session, user)
    if not (employee := bound_user.employee):
        return ValidationException(ValidationExceptionType.NOT_EMPLOYEE, HTTPStatus.FORBIDDEN)

    company = RequestHelper.get_company_of_employee(employee)

    if (extra and (ee := extra.get('editor_email')) and ee != employee.user_email):
        return ValidationException(
            ValidationExceptionType.NOT_ENOUGH_PERMISSIONS,
            HTTPStatus.FORBIDDEN,
            "You can't edit literature from other's name"
        )

    if employee.establishment.company.global_access_company:
        return None

    employee_company = RequestHelper.get_company_of_employee(employee)
    if (literature.company_id != employee_company.id
            or
            extra and (ci := extra.get('company_id')) and ci != \
            employee_company.id):
        # non existing case
        return ValidationException(
            ValidationExceptionType.NOT_ENOUGH_PERMISSIONS,
            HTTPStatus.FORBIDDEN,
            'Companies mismatch'
        )


def validate_IsUserCanReadAny(user: User, session: Session) -> ValidationException | None:
    bound_user = RequestHelper.get_current_bound_user(session, user)
    if not is_user_can_fully_read_any_literature(bound_user, session):
        return ValidationException(
            ValidationExceptionType.NO_BOOKINGS_AVAILABLE, HTTPStatus.FORBIDDEN
        )


def entryEdit_userOnly(data: ValidatorsData[Literature, User]):
    data.extend_UserValidator(validate_IsUserCanReadAny)
    pass


def entryEdit_forPdfReading(data: ValidatorsData[Literature, User]):
    data.extend_UserValidator(validate_IsUserCanReadAny)
    data.extend_DataWithUserValidator(validate_IsLiteratureCanBeFullyRead)
    pass


def entryEdit_forEditing(data: ValidatorsData[Literature, User]):
    data.extend_UserValidator(validate_IsUserCanReadAny)
    data.extend_DataWithUserValidator(validate_IsLiteratureCanBeEdited)
    pass


def is_user_can_fully_read_any_literature(bound_user: User, session: Session) -> bool:
    if bound_user.employee:
        return True

    available_active_bookings = BookingsQueryHelper().availableActiveBookings()(session.query(Booking)).first()
    if not available_active_bookings:
        return False

    return True


def availableLiteratures_ForEmployeeToRead(result: Query, employee: Employee) -> Query:
    return result.join(Company).where(
        or_(
            Company.global_access_company == True,
            Company.id == employee.establishment.company_id
        )
    )


def availableLiteratures_ForEmployeeToEdit(result: Query, employee: Employee) -> Query:
    return result.join(Company).where(
        Company.id == employee.establishment.company_id
    )


def availableLiteratures_ForUser(result: Query, bound_user: User, session: Session) -> Query:
    available_active_bookings = BookingsQueryHelper(lambda: bound_user).availableActiveBookings()(
        session.query(
            Booking
        )
    ).subquery()
    companies_ids = (
        select(distinct(Company.id))
        .where(
            or_(
                Company.global_access_company == True,
                Company.id.in_(
                    select(distinct(Company.id))
                    .join(Establishment)
                    .join(Room)
                    .join(available_active_bookings, available_active_bookings.c.room_id == Room.id)
                )
            )
        )
    )
    return result.join(Company).where(Company.id.in_(companies_ids))


def multi_genre_filtering_query_mod(query: Query, request_data: dict[str, any]) -> Query:
    genres = request.args.getlist('having_genre')
    for genre in genres:
        query = query.where(Literature.genres.any(Genre.name.like(f"%{genre}%")))
    return query
