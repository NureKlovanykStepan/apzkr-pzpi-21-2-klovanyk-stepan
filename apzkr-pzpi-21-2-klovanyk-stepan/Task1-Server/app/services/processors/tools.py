from __future__ import annotations

import datetime
from http import HTTPStatus

from flask_sqlalchemy.session import Session
from sqlalchemy import update, delete

from app.database.models import Company, Employee, Base, Establishment, User, Booking
from app.utils.extra import AlchemyExtras, ExtraValidatorsStorageBase
from app.services.decorators.query_args.serialization import RequestArgsParser
from app.services.processors.serialization import CombinedColumnFilterBuilder, Serializer2Builder, \
    CombinedColumnFilter
from app.services.validators.base import ValidationException, ValidationExceptionType


class RequestHelper:

    @staticmethod
    def is_company_global(company: Company) -> bool:
        return company.global_access_company

    @staticmethod
    def get_company_of_employee(employee: Employee) -> Company:
        return employee.establishment.company

    @staticmethod
    def get_basic_modifiers(
            builder: CombinedColumnFilterBuilder, serialization_modifiers: RequestArgsParser.Result
    ):
        return builder.include_tables(*serialization_modifiers.included_tables).exclude_tables(
            *serialization_modifiers.excluded_tables
        ).include_columns(
            *serialization_modifiers.included_columns
        ).exclude_columns(
            *serialization_modifiers.excluded_columns
        ).build()

    @staticmethod
    def get_general_serializer(
            data: Base | list[Base],
            serialization_modifiers: RequestArgsParser.Result,
            requestor: User,
            session: Session,
            extra_validation_data_storage: type[ExtraValidatorsStorageBase] | None = None
    ):
        def modifiers(builder: CombinedColumnFilterBuilder) \
                -> CombinedColumnFilter:
            return RequestHelper.get_basic_modifiers(builder, serialization_modifiers)

        return (Serializer2Builder()
                .apply_initial_data(data)
                .apply_modifiers(modifiers)
                .define_requestor(requestor)
                .apply_extra_validation_data_storage(extra_validation_data_storage)
                .apply_session(session)
                .build()
                )

    @staticmethod
    def insert_into_db(session: Session, object_to_add: Base):
        session.add(object_to_add)
        session.commit()

    @staticmethod
    def update_to_db(session: Session, object_to_update: Base, object_update_data: dict[str, any]):
        session.execute(
            update(object_to_update.__class__).where(*AlchemyExtras().get_where_clause(object_to_update)).values(
                **object_update_data
            )
        )
        session.commit()

    @staticmethod
    def delete_from_db(session: Session, object_to_delete: Base):
        session.execute(
            delete(object_to_delete.__class__).where(
                *AlchemyExtras().get_where_clause(object_to_delete)
            )
        )
        session.commit()

    @staticmethod
    def is_employee_company_global(employee: Employee) -> bool:
        return employee.establishment.company.global_access_company

    @staticmethod
    def get_company_by_establishment_id(session: any, establishment_id: int) -> Company:
        return session.get(Establishment, establishment_id).company

    @classmethod
    def get_current_date(cls):
        return datetime.datetime.now(datetime.UTC)

    @staticmethod
    def get_current_bound_user(session: Session, user: User):
        return session.get(User, {col.key: getattr(user, col.key) for col in AlchemyExtras().get_pk_of(User)})

    @staticmethod
    def get_user_current_bookings(session: Session, user: User):
        return session.query(Booking).where(
            Booking.users.any(email=user.email), Booking.expiration_time >= RequestHelper.get_current_date()
        )

    @staticmethod
    def validate_global_company_of_employee(employee: Employee):
        if not RequestHelper.get_company_of_employee(employee).global_access_company:
            raise ValidationException(ValidationExceptionType.NOT_ENOUGH_PERMISSIONS, HTTPStatus.FORBIDDEN)

    @staticmethod
    def validate_same_company_or_global(requestor_employee: Employee, target_company_id: int):
        requestor_employee_company: Company = RequestHelper.get_company_of_employee(requestor_employee)
        if requestor_employee_company.global_access_company:
            return
        if requestor_employee_company.id != target_company_id:
            raise ValidationException(ValidationExceptionType.EMPLOYEE_COMPANY_MISMATCH, HTTPStatus.BAD_REQUEST)
