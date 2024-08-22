/*
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
    bookings: Mapped[list['Booking']] = relationship('Booking', back_populates='establishment')


 */


import Company from "./Company";
import Employee from "./Employee";

class Establishment {

  constructor(data, backref_employees=null, backref_company=null, backref_country=null) {
    this.id = data.id;
    this.address = data.address;
    this.company_id = data.company_id;
    this.country_id = data.country_id;
    this.company = backref_company ? backref_company : (data.company ? new Company(data.company, this) : null);
    this.rooms = data.rooms;
    this.employees = backref_employees ? backref_employees : (data.employees ? data.employees.map(employee => new Employee(employee, this)) : []);
    this.bookings = data.bookings;
  }
}


export default Establishment