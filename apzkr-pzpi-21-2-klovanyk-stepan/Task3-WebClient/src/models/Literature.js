/*
class Literature(Base):
    """
    Represents a literature of the system.

    :var id: :class:`int` - [PK] ID
    :var name: :class:`str` - Name
    :var description: :class:`str` - Description
    :var pages: :class:`int` - Pages
    :var min_age: :class:`Optional` of :class:`int` - Min age
    :var pdf_PATH: :class:`Optional` of :class:`str` - Pdf path
    :var thumbnail_PATH: :class:`Optional` of :class:`str` - Thumbnail path
    :var editor_email: :class:`Optional` of :class:`str` - Editor email

    :var type_name: :class:`str` - [FK] :class:`LiteratureType` name

    :var type: :class:`LiteratureType` - LiteratureType as reference
    :var authors: :class:`list` of :class:`Author` - Authors as references
    :var genres: :class:`list` of :class:`Author` - Genres as references
    """
    __tablename__ = "literature"
    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(255))
    description: Mapped[str] = mapped_column(TEXT)
    pages: Mapped[Optional[int]] = mapped_column(INT)
    min_age: Mapped[Optional[int]] = mapped_column(INT)
    pdf_PATH: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
    thumbnail_PATH: Mapped[Optional[str]] = mapped_column(VARCHAR(255))
    editor_email: Mapped[Optional[str]] = mapped_column(ForeignKey('employee.user_email', ondelete='SET NULL'))
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey('company.id', ondelete='SET NULL'))

    company: Mapped['Company'] = relationship('Company', back_populates='literatures')

    type_name: Mapped[str] = mapped_column(CascadeForeignKey('literature_type.name'))

    type: Mapped['LiteratureType'] = relationship('LiteratureType', back_populates='literatures')
    authors: Mapped[list['Author']] = relationship(
        'Author', secondary='literature_author', back_populates='literatures'
    )
    genres: Mapped[list['Author']] = relationship(
        'Author', secondary='literature_genre', back_populates='literatures'
    )
    page_configs: Mapped[list['LiteraturePageConfig']] = relationship(
        'LiteraturePageConfig', back_populates='literature'
    )
    editor: Mapped['Employee'] = relationship('Employee', back_populates='edited_literatures')
 */

import {API} from "../App";
import Author from "./Author";

export default class Literature {
    constructor(data) {
        this.id = data.id;
        this.name = data.name;
        this.description = data.description;
        this.pages = data.pages;
        this.min_age = data.min_age;
        this.pdf_PATH = data.pdf_PATH;
        this.thumbnail_PATH = data.thumbnail_PATH;
        this.editor_email = data.editor_email;
        this.company = data.company;
        this.type_name = data.type_name;
        this.type = data.type;
        this.authors = data.authors ? data.authors.map(author => new Author(author)) : [];
        this.genres = data.genres;
        this.page_configs = data.page_configs;
        this.editor = data.editor;
    }
}