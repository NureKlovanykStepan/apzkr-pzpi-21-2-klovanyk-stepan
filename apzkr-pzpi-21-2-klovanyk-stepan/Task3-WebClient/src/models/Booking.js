/*
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
    establishment_id: Mapped[int] = mapped_column(CascadeForeignKey('establishment.id'))

    registrator: Mapped['Employee'] = relationship('Employee', back_populates='registered_bookings')
    room: Mapped['Room'] = relationship('Room', back_populates='bookings')
    users: Mapped[list['User']] = relationship('User', back_populates='bookings', secondary='user_booking')

    establishment: Mapped['Establishment'] = relationship('Establishment', back_populates='bookings')
 */

class Booking {
    constructor(data) {
        this.id = data.id
        this.registration_time = data.registration_time
        this.expiration_time = data.expiration_time
        this.registrator_email = data.registrator_email
        this.room_id = data.room_id
        this.registrator = data.registrator
        this.room = data.room
        this.users = data.users
    }
}

export default Booking