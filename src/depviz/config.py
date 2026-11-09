"""Загрузка и проверка конфигурации инструмента из YAML-файла."""

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import yaml

PACKAGE_NAME_RE = re.compile(
    r"^([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])$"
)
ALLOWED_SCHEMES = ("http", "https")
REQUIRED_KEYS = ("package_name", "repository", "test_mode")
OPTIONAL_KEYS = ("filter_substring",)


class ConfigError(Exception):
    """Ошибка в конфигурационном файле или в значении параметра."""


@dataclass(frozen=True)
class Config:
    """Параметры, настраиваемые пользователем."""

    package_name: str
    repository: str
    test_mode: bool
    filter_substring: str

    def as_items(self):
        """Вернуть параметры в виде списка пар (ключ, значение)."""
        return [
            ("package_name", self.package_name),
            ("repository", self.repository),
            ("test_mode", self.test_mode),
            ("filter_substring", self.filter_substring),
        ]


def read_yaml(path):
    """Прочитать YAML-файл и вернуть словарь верхнего уровня."""
    if not os.path.isfile(path):
        raise ConfigError(f"конфигурационный файл не найден: {path}")
    try:
        with open(path, encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as error:
        raise ConfigError(f"некорректный YAML: {error}") from error
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigError(f"не удалось прочитать файл: {error}") from error
    if not isinstance(data, dict):
        raise ConfigError("корнем YAML должен быть словарь ключ: значение")
    return data


def check_keys(data):
    """Проверить отсутствие лишних и наличие обязательных ключей."""
    unknown = set(data) - set(REQUIRED_KEYS) - set(OPTIONAL_KEYS)
    if unknown:
        names = ", ".join(sorted(map(str, unknown)))
        raise ConfigError(f"неизвестные параметры: {names}")
    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise ConfigError(f"не заданы параметры: {', '.join(missing)}")


def validate_package_name(value):
    """Проверить имя пакета по правилам именования pip (PEP 508)."""
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("package_name: ожидается непустая строка")
    name = value.strip()
    if not PACKAGE_NAME_RE.match(name):
        raise ConfigError(f"package_name: недопустимое имя пакета '{name}'")
    return name


def validate_test_mode(value):
    """Проверить, что режим тестирования задан логическим значением."""
    if not isinstance(value, bool):
        raise ConfigError("test_mode: ожидается true или false")
    return value


def validate_repository(value, test_mode):
    """Проверить URL репозитория или путь к файлу тестового репозитория."""
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("repository: ожидается непустая строка")
    repository = value.strip()
    if test_mode:
        if not os.path.isfile(repository):
            raise ConfigError(
                f"repository: файл тестового репозитория не найден: "
                f"{repository}"
            )
        return repository
    parsed = urlparse(repository)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        raise ConfigError(
            f"repository: ожидается URL вида http(s)://..., "
            f"получено '{repository}'"
        )
    return repository


def validate_filter(value):
    """Проверить подстроку фильтрации (может быть пустой)."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ConfigError("filter_substring: ожидается строка")
    return value


def load_config(path):
    """Загрузить конфигурацию из YAML-файла и проверить все параметры."""
    data = read_yaml(path)
    check_keys(data)
    test_mode = validate_test_mode(data["test_mode"])
    return Config(
        package_name=validate_package_name(data["package_name"]),
        repository=validate_repository(data["repository"], test_mode),
        test_mode=test_mode,
        filter_substring=validate_filter(data.get("filter_substring")),
    )
