import inspect

from flask import Blueprint

from app.database.models import Base
from app.secret_config import SecretConfig
from app.utils.extra import BlueprintsStorage, ExtraValidatorsStorageBase
from app.services.creators.builders.routes import RoutesBuilder, RequestModifiers


class BlueprintBuilder:
    def __init__(self, universal_prefix: str):
        universal_prefix = universal_prefix
        caller_root = inspect.getmodule(inspect.stack()[1].frame).__name__
        self.blueprint = Blueprint(
            universal_prefix,
            caller_root,
            url_prefix=f'{SecretConfig().API_PREFIX}/{universal_prefix}'
        )

    def register(self, storage: BlueprintsStorage):
        storage.register(self.blueprint)
        return self

    def build(self):
        return self.blueprint

    def toRoutesBuilder(self, base_type: type[Base]):
        return RoutesBuilder(self.blueprint, base_type)


class BlueprintDefaults:
    def __init__(
            self,
            universal_name: str,
            base_type: type[Base],
            extra_validator_storage: type[ExtraValidatorsStorageBase] =
            None
    ):
        self.universal_name = universal_name
        self.base_type = base_type
        self.extra_validators_storage = extra_validator_storage

    def default(self):
        return self.default_no_login().modifiers_Use(RequestModifiers.LOGIN)

    def default_no_login(self):
        name = self.universal_name
        base_type = self.base_type
        return (BlueprintBuilder(name)
                .register(BlueprintsStorage())
                .toRoutesBuilder(base_type)
                .useDefault_ValidationExceptionHandler()
                .use_ValidationDataStorage(self.extra_validators_storage))
