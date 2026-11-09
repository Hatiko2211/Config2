"""Тесты разбора зависимостей и работы с PyPI (этап 2)."""

import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from depviz import pypi  # noqa: E402
from depviz.__main__ import main  # noqa: E402
from depviz.requirements import (  # noqa: E402
    is_optional,
    normalize_name,
    parse_requirement,
)

REPO = "https://pypi.org/pypi"
REQUESTS_DIST = [
    "charset_normalizer<4,>=2",
    "idna<4,>=2.5",
    "urllib3<3,>=1.26",
    "certifi>=2017.4.17",
    'PySocks!=1.5.7,>=1.5.6; extra == "socks"',
]


def fake_response(payload):
    """Сделать объект, похожий на ответ urlopen, с JSON-телом."""
    body = io.BytesIO(json.dumps(payload).encode("utf-8"))
    response = mock.MagicMock()
    response.__enter__.return_value = body
    return response


def http_error(code):
    """Создать исключение HTTPError с заданным кодом."""
    return urllib.error.HTTPError(REPO, code, "error", {}, None)


class RequirementTestCase(unittest.TestCase):
    """Разбор строк Requires-Dist."""

    def test_simple(self):
        """Имя и ограничение версии."""
        req = parse_requirement("charset_normalizer<4,>=2")
        self.assertEqual(req.name, "charset-normalizer")
        self.assertEqual(req.specifier, "<4,>=2")
        self.assertEqual(req.marker, "")

    def test_parentheses_and_extras(self):
        """Старый формат со скобками и extras у зависимости."""
        req = parse_requirement("Foo.Bar[cli] (>=1.0, <2)")
        self.assertEqual(req.name, "foo-bar")
        self.assertEqual(req.specifier, ">=1.0,<2")

    def test_marker(self):
        """Маркер окружения сохраняется."""
        req = parse_requirement('tomli>=1; python_version < "3.11"')
        self.assertEqual(req.marker, 'python_version < "3.11"')
        self.assertFalse(is_optional(req))

    def test_extra_is_optional(self):
        """Зависимость для extra считается необязательной."""
        req = parse_requirement('PySocks>=1.5; extra == "socks"')
        self.assertTrue(is_optional(req))

    def test_url_requirement(self):
        """Зависимость по прямой ссылке: версия не указывается."""
        req = parse_requirement("pkg @ https://example.com/pkg.zip")
        self.assertEqual((req.name, req.specifier), ("pkg", ""))

    def test_invalid(self):
        """Строка без имени пакета."""
        self.assertIsNone(parse_requirement(">=1.0"))

    def test_normalize(self):
        """Нормализация имени по PEP 503."""
        self.assertEqual(normalize_name("Zope.Interface__X"),
                         "zope-interface-x")


class PypiTestCase(unittest.TestCase):
    """Получение прямых зависимостей с подменой сети."""

    def get(self, payload):
        """Вызвать get_direct_dependencies с поддельным ответом."""
        with mock.patch("urllib.request.urlopen",
                        return_value=fake_response(payload)) as urlopen:
            result = pypi.get_direct_dependencies(REPO + "/", "requests")
        self.urlopen = urlopen
        return result

    def test_direct_dependencies(self):
        """Обязательные зависимости по алфавиту, без extras."""
        deps = self.get({"info": {"requires_dist": REQUESTS_DIST}})
        self.assertEqual([d.name for d in deps], [
            "certifi", "charset-normalizer", "idna", "urllib3",
        ])
        url = self.urlopen.call_args[0][0].full_url
        self.assertEqual(url, "https://pypi.org/pypi/requests/json")

    def test_no_dependencies(self):
        """requires_dist равен null — зависимостей нет."""
        self.assertEqual(self.get({"info": {"requires_dist": None}}), [])

    def test_duplicates(self):
        """Повторяющиеся зависимости выводятся один раз."""
        deps = self.get({"info": {"requires_dist": ["a>1", "A<3"]}})
        self.assertEqual(len(deps), 1)

    def test_bad_format(self):
        """В ответе нет раздела info."""
        with self.assertRaises(pypi.RepositoryError):
            self.get({"message": "oops"})

    def test_not_found(self):
        """Пакет отсутствует в репозитории (HTTP 404)."""
        with mock.patch("urllib.request.urlopen",
                        side_effect=http_error(404)):
            with self.assertRaisesRegex(pypi.RepositoryError, "не найден"):
                pypi.get_direct_dependencies(REPO, "no-such-pkg")

    def test_server_error(self):
        """Ошибка сервера (HTTP 500)."""
        with mock.patch("urllib.request.urlopen",
                        side_effect=http_error(500)):
            with self.assertRaisesRegex(pypi.RepositoryError, "500"):
                pypi.get_direct_dependencies(REPO, "requests")

    def test_no_connection(self):
        """Репозиторий недоступен."""
        error = urllib.error.URLError("no route")
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(pypi.RepositoryError, "подключ"):
                pypi.get_direct_dependencies(REPO, "requests")

    def test_not_json(self):
        """Ответ не является JSON."""
        response = mock.MagicMock()
        response.__enter__.return_value = io.BytesIO(b"<html>")
        with mock.patch("urllib.request.urlopen", return_value=response):
            with self.assertRaisesRegex(pypi.RepositoryError, "JSON"):
                pypi.get_direct_dependencies(REPO, "requests")


class MainTestCase(unittest.TestCase):
    """Проверки вывода CLI."""

    def run_main(self, text, packages=None):
        """Запустить CLI с конфигурацией text; вернуть код, stdout, stderr.

        packages — словарь имя пакета -> список requires_dist,
        по которому подменяются ответы репозитория.
        """
        packages = packages or {}

        def respond(request, timeout=None):
            """Вернуть поддельный ответ по имени пакета из URL."""
            name = request.full_url.rstrip("/").split("/")[-2]
            if name not in packages:
                raise http_error(404)
            return fake_response({"info": {"requires_dist": packages[name]}})

        out, err = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "c.yaml")
            with open(path, "w", encoding="utf-8") as file:
                file.write(text)
            with mock.patch("urllib.request.urlopen", side_effect=respond), \
                    redirect_stdout(out), redirect_stderr(err):
                code = main(["--config", path])
        return code, out.getvalue(), err.getvalue()

    def test_prints_graph(self):
        """Выводится граф с транзитивными зависимостями, без extras."""
        text = f"package_name: Requests\nrepository: {REPO}\n" \
               "test_mode: false\nfilter_substring: cert\n"
        packages = {
            "requests": REQUESTS_DIST, "idna": [], "certifi": [],
            "charset-normalizer": [], "urllib3": ["idna>=2"],
        }
        code, out, _ = self.run_main(text, packages)
        lines = out.splitlines()
        self.assertEqual(code, 0)
        self.assertIn("  requests -> charset-normalizer, idna, urllib3",
                      lines)
        self.assertIn("  urllib3 -> idna", lines)
        self.assertIn("исключены: certifi", out)
        self.assertNotIn("pysocks", out)

    def test_transitive_not_found(self):
        """Ошибка при загрузке транзитивной зависимости — код 2."""
        text = f"package_name: a\nrepository: {REPO}\ntest_mode: false\n"
        code, _, err = self.run_main(text, {"a": ["b"]})
        self.assertEqual(code, 2)
        self.assertIn("пакет не найден", err)

    def test_test_mode(self):
        """Тестовый репозиторий из examples: цикл обнаружен."""
        repo = os.path.join(ROOT, "examples", "repos", "cycle.txt")
        text = f"package_name: A\nrepository: '{repo}'\ntest_mode: true\n"
        code, out, _ = self.run_main(text)
        self.assertEqual(code, 0)
        self.assertIn("  A -> B -> C -> A", out.splitlines())

    def test_config_error(self):
        """Ошибка конфигурации — код 1."""
        code, _, err = self.run_main("- not a mapping\n")
        self.assertEqual(code, 1)
        self.assertIn("Ошибка конфигурации", err)


if __name__ == "__main__":
    unittest.main()
