/*
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

 */

import Establishment from "./Establishment";

class Company {
  constructor(data, backref_establishments=null, backref_literatures=null) {
    this.id = data.id;
    this.name = data.name;
    this.global_access_company = data.global_access_company;
    this.establishments = backref_establishments ? backref_establishments : (data.establishments ? data.establishments.map(establishment => new Establishment(establishment, this)) : []);
    this.literatures = data.literatures;
  }
}

export default Company