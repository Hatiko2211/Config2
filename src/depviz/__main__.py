"""Точка входа CLI: python -m depviz --config <файл>."""

import argparse
import sys

from depviz.config import ConfigError, load_config
from depviz.graph import build_graph, find_cycles
from depviz.pypi import RepositoryError
from depviz.sources import make_source

DEFAULT_CONFIG = "config.yaml"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 1
EXIT_REPOSITORY_ERROR = 2
NO_DEPENDENCIES = "(нет зависимостей)"


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


def print_header(config, graph):
    """Вывести, для какого пакета, откуда и с каким фильтром строится граф."""
    mode = "тестовый репозиторий" if config.test_mode else "репозиторий"
    print(f"Граф зависимостей пакета {graph.root}")
    print(f"  {mode}: {config.repository}")
    if config.filter_substring:
        excluded = ", ".join(sorted(graph.excluded)) or "нет"
        print(f"  фильтр: '{config.filter_substring}' "
              f"(исключены: {excluded})")


def print_edges(graph):
    """Вывести пакеты в порядке обхода BFS и их зависимости."""
    if not graph.edges:
        print("  корневой пакет исключён фильтром, граф пуст")
    for package, deps in graph.edges.items():
        print(f"  {package} -> {', '.join(deps) or NO_DEPENDENCIES}")


def print_cycles(cycles):
    """Вывести найденные циклические зависимости."""
    if not cycles:
        print("Циклических зависимостей нет")
        return
    print("Циклические зависимости:")
    for cycle in cycles:
        print(f"  {' -> '.join(cycle)}")


def run(config):
    """Построить граф зависимостей и вывести его; вернуть код завершения."""
    try:
        root, get_dependencies = make_source(config)
        graph = build_graph(root, get_dependencies, config.filter_substring)
    except RepositoryError as error:
        print(f"Ошибка репозитория: {error}", file=sys.stderr)
        return EXIT_REPOSITORY_ERROR
    print_header(config, graph)
    print_edges(graph)
    print_cycles(find_cycles(graph))
    return EXIT_OK


def main(argv=None):
    """Загрузить конфигурацию, построить и вывести граф зависимостей."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    return run(config)


if __name__ == "__main__":
    sys.exit(main())
