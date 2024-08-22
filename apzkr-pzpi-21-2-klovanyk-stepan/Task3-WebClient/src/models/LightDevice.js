/*
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

    light_type_name: Mapped[Optional[str]] = mapped_column(CHAR(20), CascadeForeignKey('light_type.name'))
    room_id: Mapped[Optional[int]] = mapped_column(CascadeForeignKey('room.id'))
    details: Mapped[Optional[str]] = mapped_column(VARCHAR(255))

    light_type: Mapped[Optional['LightType']] = relationship('LightType', back_populates='light_devices')
    room: Mapped[Optional['Room']] = relationship('Room', back_populates='light_devices')
 */

export default class LightDevice {
    constructor(data) {
        this.id = data.id
        this.port = data.port
        this.light_type_name = data.light_type_name
        this.room_id = data.room_id
        this.details = data.details
    }
}