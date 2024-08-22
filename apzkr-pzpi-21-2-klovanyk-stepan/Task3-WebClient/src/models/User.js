/*
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

 */

import Employee from "./Employee";

class User {
  constructor(data, backref_employee=null) {
    this.email = data.email;
    this.nickname = data.nickname;
    this.real_name = data.real_name;
    this.real_surname = data.real_surname;
    this.phone_number = data.phone_number;
    this.password_hash = data.password_hash;
    this.country_id = data.country_id;
    this.country = data.country;
    this.employee = backref_employee ? backref_employee : !data.employee ? null :(Object.hasOwn(data.employee, 'user_email') ? new Employee(data.employee, this) : null);
    this.bookings = data.bookings;
  }
}



export default User;