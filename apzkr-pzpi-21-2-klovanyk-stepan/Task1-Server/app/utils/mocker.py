import datetime
import random

from app import Globals
from app.database.models import Country, User, Employee, Company, Booking, Room, Establishment, Literature, Author, \
    Genre, LiteratureType, DeviceConfig, LightType


class MockCountry:
    def __new__(cls, name: str, code: int = None):
        return Country(name=name, code=code, charcode=name[:2].upper())


class MockUser:
    def __new__(cls, name: str, country: Country, password: str = None):
        return User(
            email=f"{name}@example.com",
            nickname=''.join(i.upper() if random.random() > 0.5 else i.lower() for i in name),
            real_name=f'{name}_name',
            real_surname=f'{name}_surname',
            phone_number=f'{random.randint(1000000000, 9999999999)}',
            password_hash=Globals().bcrypt.generate_password_hash(password if password else f'password_of_{name}'),
            country=country
        )


class MockCompany:
    def __new__(cls, name: str, global_access_company: bool = False):
        return Company(name=name, global_access_company=global_access_company)


class MockEmployee:
    def __new__(
            cls,
            user: User,
            establishment: Establishment,
            head_manager: bool = False,
            booking_manager: bool = False,
            literature_manager: bool = False,
            iot_manager: bool = False
    ):
        return Employee(
            user=user,
            establishment=establishment,
            head_manager=head_manager,
            booking_manager=booking_manager,
            literature_manager=literature_manager,
            iot_manager=iot_manager
        )


class MockBookingWithUsers:
    def __new__(
            cls,
            registrator: Employee,
            room: Room,
            user_must_have: User,
            *other_users: User,
            expires_in: datetime.timedelta = datetime.timedelta(days=1)
    ):
        return Booking(
            registration_time=datetime.datetime.now(datetime.UTC), expiration_time=datetime.datetime.now(
                datetime.UTC
            ) + expires_in, registrator=registrator, room=room, users=[user_must_have, *other_users], )


class MockEstablishment:
    def __new__(cls, address: str, company: Company, country: Country):
        return Establishment(
            address=address, company=company, country=country
        )


class MockRoom:
    def __new__(cls, label: str, establishment: Establishment):
        return Room(label=label, establishment=establishment)


class MockLiterature:
    full_genres = {}
    full_authors = {}
    full_types = {}

    @staticmethod
    def _add_and_get_model(d: dict, value: str, model: type[Author] | type[Genre] | type[LiteratureType]):
        if value not in d:
            if model == Author:
                d[value] = model(pseudonym=value)
            else:
                d[value] = model(name=value)
        return d[value]

    def __new__(
            cls,
            name: str,
            desc: str,
            genres: list[str],
            authors: list[str],
            min_age: int,
            pages: int,
            type_: str,
            editor: Employee,
            company: Company
    ):
        return Literature(
            name=name,
            description=desc,
            pages=pages,
            min_age=min_age,
            pdf_PATH=None,
            thumbnail_PATH=None,
            editor=editor,
            company=company,
            type=cls._add_and_get_model(cls.full_types, type_, LiteratureType),
            genres=[cls._add_and_get_model(cls.full_genres, g, Genre) for g in genres],
            authors=[cls._add_and_get_model(cls.full_authors, a, Author) for a in authors]
        )


class MockStation:
    @staticmethod
    def BasicWithRelations(admin_name: str = 'admin'):
        countries = {
            'Ukraine': MockCountry('Ukraine', 380), 'USA': MockCountry('USA', 1), 'Poland': MockCountry('Poland', 48)
        }

        companies = {
            'FeelTheBook': MockCompany('FeelTheBook', True),
            'Company1': MockCompany('Company1', False),
            'Company2': MockCompany('Company2', False)
        }

        establishments: dict[str, Establishment] = {
            'FtB_main_office': MockEstablishment(
                'FtB_main_office_address', companies['FeelTheBook'], countries['Ukraine']
            ),
            'US_partner_hotel': MockEstablishment('US_partner_office_address', companies['Company1'], countries['USA']),
            'Poland_partner_hotel': MockEstablishment(
                'Poland_partner_office_address', companies['Company2'], countries['Poland']
            ),
            'Poland_partner_hotel_2': MockEstablishment(
                'Poland_partner_office_2_address', companies['Company2'], countries['Poland']
            )
        }

        rooms = [MockRoom(f"room_{establishment.address}_{r}", establishment) for establishment, rooms_count in {
            establishments['FtB_main_office']: 10,
            establishments['US_partner_hotel']: 100,
            establishments['Poland_partner_hotel']: 50,
            establishments['Poland_partner_hotel_2']: 46
        }.items() for r in range(0, rooms_count)]

        users = {
            "customer1": MockUser("customer1", countries['Ukraine']),
            "customer2": MockUser("customer2", countries['Ukraine']),
            "customer3": MockUser("customer3", countries['Poland']),
            "owner": MockUser("admin", countries['Ukraine'], 'admin'),
            "global_booking_manager": MockUser("gbm", countries['Ukraine'], 'gbm'),
            "global_literature_manager": MockUser("glm", countries['Ukraine'], 'glm'),
            "global_iot_manager": MockUser("gim", countries['Ukraine'], 'gim'),
            "local_head_manager": MockUser("lhm", countries['Ukraine'], 'lhm'),
            "local_booking_manager": MockUser("lbm", countries['Ukraine'], 'lbm'),
            "local_literature_manager": MockUser("llm", countries['Ukraine'], 'llm'),
            "local_iot_manager": MockUser("lim", countries['Ukraine'], 'lim')
        }

        employees = {
            "admin": MockEmployee(users['owner'], establishments['FtB_main_office'], True, True, True, True),
            "gbm": MockEmployee(
                users['global_booking_manager'], establishments['FtB_main_office'], False, True, False, False
            ),
            "glm": MockEmployee(
                users['global_literature_manager'], establishments['FtB_main_office'], False, False, True, False
            ),
            "gim": MockEmployee(
                users['global_iot_manager'], establishments['FtB_main_office'], False, False, False, True
            ),
            "lhm": MockEmployee(
                users['local_head_manager'], establishments['US_partner_hotel'], True, True, False, False
            ),
            "lbm": MockEmployee(
                users['local_booking_manager'], establishments['US_partner_hotel'], False, True, False, False
            ),
            "llm": MockEmployee(
                users['local_literature_manager'], establishments['Poland_partner_hotel'], False, False, True, False
            ),
            "lim": MockEmployee(
                users['local_iot_manager'], establishments['Poland_partner_hotel_2'], False, False, False, True
            )
        }

        bookings = [
            MockBookingWithUsers(
                registrator=employees['lbm'],
                room=[room for room in rooms if room.establishment == establishments['US_partner_hotel']][0],
                user_must_have=users['customer1'],
                expires_in=datetime.timedelta(days=1),
            ),
            MockBookingWithUsers(
                employees['gbm'],
                rooms[0],
                users['customer2'],
                users['customer3'],
                expires_in=datetime.timedelta(days=999),
            )]

        literatures = [MockLiterature(
            "The Lord of the Rings",
            "An epic high fantasy adventure following a hobbit's quest to destroy the One Ring.",
            ["Fantasy", "Adventure", "Epic"],
            ["J. R. R. Tolkien"],
            12,
            1178,
            "Novel",
            employees["glm"],
            companies["FeelTheBook"]
        ), MockLiterature(
            "The Odyssey",
            "An epic poem about Odysseus's ten-year journey home after the Trojan War.",
            ["Poetry", "Epic", "Adventure", "Mythology"],
            ["Homer"],
            14,
            None,
            "Epic poem",
            employees["glm"],
            companies["FeelTheBook"]
        ), MockLiterature(
            "Good Omens",
            "A humorous fantasy novel about an angel and a demon trying to prevent the apocalypse.",
            ["Humor", "Fantasy", "Apocalyptic"],
            ["Terry Pratchett", "Neil Gaiman"],
            14,
            None,
            "Novel",
            employees["glm"],
            companies["FeelTheBook"]
        ), MockLiterature(
            "Horimiya",
            "Hori tries to seem like an ordinary high school student, while in fact she devotes all "
            "her time to taking care of the house. The girl has to take the place of her younger "
            "brother in the family, cleaning, laundry and other household chores. One day she meets a man "
            "who, just like her, tries not to reveal his true personality at school: Miyamura, "
            "a silent guy with glasses. Now the two of them have someone to share and reveal their true "
            "selves without fear of being found out at school. ",
            ["Comedy", "Romance", "School", "Everyday life"],
            ["HERO"],
            16,
            None,
            "Manga",
            employees["llm"],
            companies["Company2"]
        ), ]

        genres = ['Comedy', 'Romance', 'School', 'Everyday life', 'Fantasy', 'Adventure', 'Epic', 'Mythology', 'Poetry',
                  'Humor', 'Apocalypse']

        import random

        literatures += [MockLiterature(
            f"Name-{random.randint(0, 100000)}",
            f"Description-{random.randint(0, 100000)}",
            list(random.sample(genres, random.randint(2, 5))),
            [f"Author-{random.randint(0, 1000)}", random.random() > 0.9 and f"Author-{random.randint(0, 1000)}"],
            random.choice([None, 4, 8, 6, 14, 16, 18, 21]),
            None,
            random.choice(["Manga", "Novel", "Poem", "Epic poem", "Poetry"]), employees["llm"],
            random.choice(list(companies.values()))
        ) for _ in range(450)]

        light_types = [LightType(name=t) for t in list(DeviceConfig.DeviceType)]

        return [*countries.values(), *companies.values(), *establishments.values(), *rooms, *users.values(),
                *employees.values(), *bookings, *MockLiterature.full_types.values(),
                *MockLiterature.full_genres.values(), *MockLiterature.full_authors.values(), *literatures, *light_types]
