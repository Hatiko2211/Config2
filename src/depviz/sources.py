"""Выбор источника зависимостей: PyPI по URL или тестовый репозиторий."""

from depviz.pypi import RepositoryError, get_direct_dependencies
from depviz.requirements import normalize_name
from depviz.testrepo import load_test_repository


def file_source(config):
    """Источник из файла тестового репозитория: (корень, функция)."""
    packages = load_test_repository(config.repository)
    if config.package_name not in packages:
        raise RepositoryError(
            f"пакет {config.package_name} не описан в тестовом "
            f"репозитории {config.repository}"
        )
    return config.package_name, lambda name: packages.get(name, [])


def pypi_source(config):
    """Источник из репозитория PyPI по URL: (корень, функция)."""
    def dependencies(name):
        """Вернуть имена прямых зависимостей пакета из репозитория."""
        found = get_direct_dependencies(config.repository, name)
        return [requirement.name for requirement in found]

    return normalize_name(config.package_name), dependencies


def make_source(config):
    """Вернуть корневой пакет и функцию получения его зависимостей."""
    if config.test_mode:
        return file_source(config)
    return pypi_source(config)
