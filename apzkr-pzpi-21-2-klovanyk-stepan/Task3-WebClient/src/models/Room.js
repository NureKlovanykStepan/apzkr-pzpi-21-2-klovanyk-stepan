/*
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
 */

class Room {
    constructor(room) {
        this.id = room.id;
        this.label = room.label;
        this.establishment = room.establishment;
        this.light_devices = room.light_devices;
        this.bookings = room.bookings;
    }
}

export default Room