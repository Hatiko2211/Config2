"""Точка входа CLI: python -m depviz --config <файл>."""

import argparse
import sys

from depviz.config import ConfigError, load_config
from depviz.pypi import RepositoryError, get_direct_dependencies

DEFAULT_CONFIG = "config.yaml"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 1
EXIT_REPOSITORY_ERROR = 2
EXIT_NOT_SUPPORTED = 3


def parse_args(argv):
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализация графа зависимостей pip-пакетов.",
    )
    parser.add_argument(
        "-c", "--config",
        default=DEFAULT_CONFIG,
        help=f"путь к YAML-конфигурации (по умолчанию {DEFAULT_CONFIG})",
    )
    return parser.parse_args(argv)


def format_requirement(requirement):
    """Сформировать строку вида 'имя ограничение ; маркер'."""
    parts = [requirement.name]
    if requirement.specifier:
        parts.append(requirement.specifier)
    if requirement.marker:
        parts.append(f"; {requirement.marker}")
    return " ".join(parts)


def print_dependencies(config, dependencies):
    """Вывести прямые зависимости пакета."""
    print(f"Прямые зависимости пакета {config.package_name} "
          f"({config.repository}):")
    if not dependencies:
        print("  нет прямых зависимостей")
    for requirement in dependencies:
        print(f"  {format_requirement(requirement)}")


def run(config):
    """Получить и вывести прямые зависимости; вернуть код завершения."""
    if config.test_mode:
        print("Режим тестового репозитория будет реализован на этапе 3",
              file=sys.stderr)
        return EXIT_NOT_SUPPORTED
    try:
        dependencies = get_direct_dependencies(
            config.repository, config.package_name
        )
    except RepositoryError as error:
        print(f"Ошибка репозитория: {error}", file=sys.stderr)
        return EXIT_REPOSITORY_ERROR
    print_dependencies(config, dependencies)
    return EXIT_OK


def main(argv=None):
    """Загрузить конфигурацию и вывести прямые зависимости пакета."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    return run(config)


if __name__ == "__main__":
    sys.exit(main())
