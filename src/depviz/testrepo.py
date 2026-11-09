"""Чтение файла тестового репозитория.

Формат файла: одна строка на пакет, ``ПАКЕТ: ЗАВИСИМОСТЬ ЗАВИСИМОСТЬ ...``.
Имена пакетов — большие латинские буквы. Пустые строки и строки,
начинающиеся с ``#``, пропускаются. Пакет, который упоминается
только как зависимость, считается пакетом без зависимостей.
"""

import re

from depviz.pypi import RepositoryError

NAME_RE = re.compile(r"^[A-Z]+$")
COMMENT_PREFIX = "#"


def check_name(name, number):
    """Проверить, что имя пакета состоит из больших латинских букв."""
    if not NAME_RE.match(name):
        raise RepositoryError(
            f"строка {number}: имя пакета '{name}' должно состоять "
            f"из больших латинских букв"
        )
    return name


def parse_line(line, number):
    """Разобрать строку 'ПАКЕТ: ЗАВИСИМОСТИ'; None для пустой строки."""
    text = line.strip()
    if not text or text.startswith(COMMENT_PREFIX):
        return None
    if ":" not in text:
        raise RepositoryError(
            f"строка {number}: ожидается 'ПАКЕТ: ЗАВИСИМОСТИ', "
            f"получено '{text}'"
        )
    head, _, tail = text.partition(":")
    name = check_name(head.strip(), number)
    deps = []
    for dep in tail.split():
        if check_name(dep, number) not in deps:
            deps.append(dep)
    return name, deps


def read_lines(path):
    """Прочитать строки файла тестового репозитория."""
    try:
        with open(path, encoding="utf-8") as file:
            return file.readlines()
    except (OSError, UnicodeDecodeError) as error:
        raise RepositoryError(
            f"не удалось прочитать тестовый репозиторий: {error}"
        ) from error


def load_test_repository(path):
    """Загрузить тестовый репозиторий: словарь пакет -> зависимости."""
    packages = {}
    for number, line in enumerate(read_lines(path), start=1):
        parsed = parse_line(line, number)
        if parsed is None:
            continue
        name, deps = parsed
        if name in packages:
            raise RepositoryError(
                f"строка {number}: пакет {name} описан повторно"
            )
        packages[name] = deps
    return packages
