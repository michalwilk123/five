import tomllib
import yaml
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError
from pydantic import field_validator


class ConfigValidationException(Exception):
    pass


class FiveProjectConfig:
    def __init__(self, config_path: str):
        self.config_path: str = config_path
        self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, "rb") as f:
                data = tomllib.load(f)
            self.settings: ConfigPydanticModel = ConfigPydanticModel.model_validate(data)
        except (tomllib.TOMLDecodeError, PydanticValidationError) as e:
            raise ConfigValidationException from e

    def get_object_by_name(self, object_name: str) -> 'Object | None':
        for obj in self.settings.objects:
            if obj.id == object_name:
                return obj
        return None


class Object(BaseModel):
    id: str
    structure: str
    examples: list[str] = Field(default_factory=list)
    globs: list[str]
    description: str | None = None


class Script(BaseModel):
    id: str
    command: str
    relations: dict | None = None  # Will be populated by parsing a YAML string

    @field_validator("relations", mode="before")
    @classmethod
    def _parse_relations_from_yaml_string(cls, v) -> dict | None:
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return yaml.safe_load(v)
            except yaml.YAMLError as e:
                raise ConfigValidationException from e
        raise ConfigValidationException(
            message=f"Invalid type for 'relations' field: expected YAML string or dict, got {type(v).__name__}."
        )


class ConfigPydanticModel(BaseModel):
    rules: str = ""
    structure: str | None = None
    examples: list[str] = Field(default_factory=list)
    override: list[str] = Field(default_factory=list)
    environment_defaults: dict[str, str] | None = None  # Defaults to None if not present
    objects: list[Object] = Field(default_factory=list)
    scripts: list[Script] = Field(default_factory=list)
