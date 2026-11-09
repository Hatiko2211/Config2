"""Получение прямых зависимостей пакета из репозитория PyPI (JSON API)."""

import json
import urllib.error
import urllib.parse
import urllib.request

from depviz.requirements import is_optional, parse_requirement

HTTP_NOT_FOUND = 404
TIMEOUT_SECONDS = 15
USER_AGENT = "depviz/0.2"


class RepositoryError(Exception):
    """Не удалось получить или разобрать данные репозитория."""


def metadata_url(repository, package):
    """Сформировать URL JSON-описания пакета: <repo>/<пакет>/json."""
    name = urllib.parse.quote(package)
    return f"{repository.rstrip('/')}/{name}/json"


def download_json(url):
    """Скачать документ по URL и разобрать его как JSON."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise RepositoryError(f"пакет не найден: {url}") from error
        raise RepositoryError(
            f"репозиторий вернул HTTP {error.code}: {url}"
        ) from error
    except (urllib.error.URLError, OSError) as error:
        raise RepositoryError(
            f"не удалось подключиться к репозиторию: {error}"
        ) from error
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RepositoryError(f"ответ не является JSON: {url}") from error


def extract_requires_dist(metadata):
    """Достать список строк Requires-Dist из JSON-описания пакета."""
    info = metadata.get("info") if isinstance(metadata, dict) else None
    if not isinstance(info, dict):
        raise RepositoryError("в ответе репозитория нет раздела info")
    requires = info.get("requires_dist") or []
    if not isinstance(requires, list):
        raise RepositoryError("поле requires_dist имеет неверный формат")
    return requires


def select_direct(requires):
    """Оставить обязательные зависимости без повторов, по алфавиту."""
    found = {}
    for line in requires:
        requirement = parse_requirement(str(line))
        if requirement is None or is_optional(requirement):
            continue
        found.setdefault(requirement.name, requirement)
    return [found[name] for name in sorted(found)]


def get_direct_dependencies(repository, package):
    """Вернуть прямые зависимости пакета из репозитория по URL."""
    metadata = download_json(metadata_url(repository, package))
    return select_direct(extract_requires_dist(metadata))
