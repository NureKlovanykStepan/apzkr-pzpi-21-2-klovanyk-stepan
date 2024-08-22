/*
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

 */

import User from "./User";
import Establishment from "./Establishment";

class Employee {
    constructor(data, backref_user=null, backref_establishment=null) {
        this.head_manager = data.head_manager;
        this.booking_manager = data.booking_manager;
        this.literature_manager = data.literature_manager;
        this.iot_manager = data.iot_manager;
        this.user_email = data.user_email;
        this.establishment_id = data.establishment_id;
        this.user = backref_user ? backref_user : (data.user ? new User(data.user, this) : null);
        this.establishment = backref_establishment ? backref_establishment : (data.establishment ? new Establishment(data.establishment, this) : null);
        this.registered_bookings = data.registered_bookings;
        this.edited_literatures = data.edited_literatures;
    }
}

export default Employee