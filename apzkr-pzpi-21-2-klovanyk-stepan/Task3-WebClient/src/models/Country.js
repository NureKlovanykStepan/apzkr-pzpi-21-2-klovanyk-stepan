/*
class Country(Base):
    """
    Represents a country of the system.

    :var id: :class:`int` - [PK] ID
    :var name: :class:`str` - Name
    :var charcode: :class:`str` - Charcode (example: UA, US, EN etc.)
    :var code: :class:`int` - Code

    :var users: :class:`list` of :class:`User` - Users as references
    :var establishments: :class:`list` of :class:`Establishment` - Establishments as references
    """
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(INT, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    charcode: Mapped[str] = mapped_column(CHAR(2))
    code: Mapped[int] = mapped_column(INT)

    users: Mapped[list['User']] = relationship('User', back_populates='country')
    establishments: Mapped[list['Establishment']] = relationship('Establishment', back_populates='country')
 */


export default class Country {
    constructor(data) {
        this.id = data.id;
        this.name = data.name;
        this.charcode = data.charcode;
        this.code = data.code;
        this.users = data.users;
        this.establishments = data.establishments;
    }
}