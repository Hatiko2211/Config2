"""Разбор строк зависимостей pip (поле Requires-Dist, PEP 508)."""

import re
from dataclasses import dataclass

NAME_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)"
    r"\s*(?:\[[^\]]*\])?"
)
EXTRA_MARKER_RE = re.compile(r"\bextra\s*==")
SEPARATOR_RE = re.compile(r"[-_.]+")


@dataclass(frozen=True)
class Requirement:
    """Одна зависимость: имя пакета, ограничение версии и маркер."""

    name: str
    specifier: str
    marker: str


def normalize_name(name):
    """Привести имя пакета к каноническому виду (PEP 503)."""
    return SEPARATOR_RE.sub("-", name).lower()


def clean_specifier(text):
    """Убрать пробелы и скобки вокруг ограничения версии."""
    spec = text.strip()
    if spec.startswith("(") and spec.endswith(")"):
        spec = spec[1:-1]
    return spec.replace(" ", "")


def parse_requirement(line):
    """Разобрать строку зависимости; вернуть None, если она некорректна."""
    body, _, marker = line.partition(";")
    match = NAME_RE.match(body)
    if match is None:
        return None
    rest = body[match.end():]
    if "@" in rest:
        rest = ""
    return Requirement(
        name=normalize_name(match.group("name")),
        specifier=clean_specifier(rest),
        marker=marker.strip(),
    )


def is_optional(requirement):
    """Зависимость нужна только для дополнительной возможности (extra)."""
    return bool(EXTRA_MARKER_RE.search(requirement.marker))
