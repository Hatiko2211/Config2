"""Тесты загрузки и проверки конфигурации (этап 1)."""

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from depviz.__main__ import main  # noqa: E402
from depviz.config import ConfigError, load_config  # noqa: E402

VALID = (
    "package_name: requests\n"
    "repository: https://pypi.org/pypi\n"
    "test_mode: false\n"
    "filter_substring: urllib\n"
)


class ConfigTestCase(unittest.TestCase):
    """Проверки функции load_config."""

    def setUp(self):
        """Создать временный каталог для конфигураций."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, text, name="config.yaml"):
        """Записать текст во временный файл и вернуть путь к нему."""
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def assert_error(self, text, fragment):
        """Убедиться, что конфигурация вызывает ConfigError с текстом."""
        with self.assertRaises(ConfigError) as ctx:
            load_config(self.write(text))
        self.assertIn(fragment, str(ctx.exception))

    def test_valid_config(self):
        """Корректная конфигурация загружается полностью."""
        config = load_config(self.write(VALID))
        self.assertEqual(config.package_name, "requests")
        self.assertEqual(config.repository, "https://pypi.org/pypi")
        self.assertFalse(config.test_mode)
        self.assertEqual(config.filter_substring, "urllib")

    def test_filter_is_optional(self):
        """Без filter_substring используется пустая строка."""
        text = VALID.replace("filter_substring: urllib\n", "")
        self.assertEqual(load_config(self.write(text)).filter_substring, "")

    def test_test_mode_with_file(self):
        """В режиме тестирования repository — путь к файлу."""
        repo = self.write("A: B\n", "repo.txt")
        text = f"package_name: A\nrepository: '{repo}'\ntest_mode: true\n"
        self.assertEqual(load_config(self.write(text)).repository, repo)

    def test_missing_file(self):
        """Отсутствующий конфигурационный файл."""
        with self.assertRaises(ConfigError):
            load_config(os.path.join(self.tmp.name, "nope.yaml"))

    def test_broken_yaml(self):
        """Синтаксическая ошибка YAML."""
        self.assert_error("package_name: [x\n", "некорректный YAML")

    def test_not_a_mapping(self):
        """Корень YAML — не словарь."""
        self.assert_error("- a\n- b\n", "словарь")

    def test_missing_key(self):
        """Не задан обязательный параметр."""
        self.assert_error("package_name: a\ntest_mode: false\n",
                          "repository")

    def test_unknown_key(self):
        """Задан неизвестный параметр."""
        self.assert_error(VALID + "depth: 3\n", "depth")

    def test_bad_package_name(self):
        """Недопустимое имя пакета."""
        text = VALID.replace("requests", "'-bad name!'")
        self.assert_error(text, "package_name")

    def test_empty_package_name(self):
        """Пустое имя пакета."""
        self.assert_error(VALID.replace("requests", "''"), "package_name")

    def test_bad_url(self):
        """Некорректный URL репозитория."""
        text = VALID.replace("https://pypi.org/pypi", "ftp:/pypi")
        self.assert_error(text, "URL")

    def test_missing_test_repo(self):
        """Файл тестового репозитория не существует."""
        text = "package_name: A\nrepository: none.txt\ntest_mode: true\n"
        self.assert_error(text, "не найден")

    def test_bad_test_mode(self):
        """Режим тестирования задан не логическим значением."""
        text = VALID.replace("test_mode: false", "test_mode: maybe")
        self.assert_error(text, "test_mode")

    def test_bad_filter(self):
        """Подстрока фильтрации задана не строкой."""
        text = VALID.replace("urllib", "42")
        self.assert_error(text, "filter_substring")


class MainTestCase(unittest.TestCase):
    """Проверки вывода CLI."""

    def test_prints_key_value(self):
        """При корректной конфигурации печатаются все параметры."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "c.yaml")
            with open(path, "w", encoding="utf-8") as file:
                file.write(VALID)
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["--config", path])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().splitlines(), [
            "package_name=requests",
            "repository=https://pypi.org/pypi",
            "test_mode=false",
            "filter_substring=urllib",
        ])

    def test_error_exit_code(self):
        """При ошибке возвращается код 1 и сообщение в stderr."""
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["--config", "no_such_config.yaml"])
        self.assertEqual(code, 1)
        self.assertIn("Ошибка конфигурации", err.getvalue())


if __name__ == "__main__":
    unittest.main()
