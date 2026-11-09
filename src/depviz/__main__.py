"""Точка входа CLI: python -m depviz --config <файл>."""

import argparse
import sys

from depviz.config import ConfigError, load_config

DEFAULT_CONFIG = "config.yaml"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 1


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


def format_value(value):
    """Преобразовать значение параметра в строку для вывода."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return value


def main(argv=None):
    """Загрузить конфигурацию и вывести параметры ключ-значение."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    for key, value in config.as_items():
        print(f"{key}={format_value(value)}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
