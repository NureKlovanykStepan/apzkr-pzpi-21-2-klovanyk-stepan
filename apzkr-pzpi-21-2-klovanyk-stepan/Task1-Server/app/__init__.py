import asyncio

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import QueuePool

from app.utils.base import SingletonMeta


class Globals(metaclass=SingletonMeta):
    def __init__(self, app: Flask | None = None):
        if app is not None:
            self.app = app
            self.db = SQLAlchemy(app)
            self.bcrypt = Bcrypt(app)
            self.login_manager = LoginManager(app)

