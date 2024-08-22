/*
class Author(Base):
    """
    Represents an author of the system.

    :var pseudonym: :class:`str` - [PK] Pseudonym
    :var name: :class:`Optional` of :class:`str` - Name
    :var surname: :class:`Optional` of :class:`str` - Surname

    :var literatures: :class:`list` of :class:`Literature` - Literatures as references
    """
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(INT, primary_key=True)
    pseudonym: Mapped[str] = mapped_column(VARCHAR(255))
    name: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
    surname: Mapped[Optional[str]] = mapped_column(VARCHAR(255))

    literatures: Mapped[list['Literature']] = relationship(
        'Literature', secondary='literature_author', back_populates='authors'
    )

 */

export default class Author
{
    constructor(data)
    {
        this.id = data.id;
        this.pseudonym = data.pseudonym;
        this.name = data.name;
        this.surname = data.surname;
    }

    equalsTo(other) {
        if (!(other instanceof Author)) return false
        if (this.pseudonym !== other.pseudonym) return false
        if (this.name !== other.name) return false
        if (this.surname !== other.surname) return false
        return true
    }

    toString()
    {
        return `${this.pseudonym}${this.name || this.surname
            ? ` (${[this.name, this.surname].join(' ').trim()})`
            : ''}`
    }

    /**
     *
     * @param {string} s
     * @returns {null}
     */
    static fromString(s)
    {
        const match = s.match(/^(.*?)\s*(?:\((.*)\))?$/)
        console.log(s, match)
        if (!match) return null
        const pseudonym = match[1]
        const name_surname = match[2]?.split(' ') ?? []
        const [name, surname] = [...Array(2)].map((
            _,
            i
        ) => name_surname[i] || null)
        return new Author({pseudonym, name, surname})
    }
}