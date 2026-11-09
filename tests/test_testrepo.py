"""Тесты чтения файла тестового репозитория (этап 3)."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from depviz.pypi import RepositoryError  # noqa: E402
from depviz.testrepo import load_test_repository  # noqa: E402


class LoadTestRepositoryTestCase(unittest.TestCase):
    """Разбор формата 'ПАКЕТ: ЗАВИСИМОСТИ'."""

    def load(self, text):
        """Записать текст во временный файл и загрузить его."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "repo.txt")
            with open(path, "w", encoding="utf-8") as file:
                file.write(text)
            return load_test_repository(path)

    def test_valid(self):
        """Комментарии и пустые строки пропускаются."""
        text = "# граф\nA: B C\n\nB: C\nC:\n"
        self.assertEqual(self.load(text),
                         {"A": ["B", "C"], "B": ["C"], "C": []})

    def test_duplicate_dependency(self):
        """Повтор зависимости в строке учитывается один раз."""
        self.assertEqual(self.load("A: B B\n"), {"A": ["B"]})

    def test_lowercase_name(self):
        """Имена только из больших латинских букв."""
        with self.assertRaisesRegex(RepositoryError, "строка 1"):
            self.load("A: b\n")

    def test_missing_colon(self):
        """Строка без двоеточия."""
        with self.assertRaisesRegex(RepositoryError, "ПАКЕТ"):
            self.load("A B\n")

    def test_duplicate_package(self):
        """Пакет описан дважды."""
        with self.assertRaisesRegex(RepositoryError, "повторно"):
            self.load("A: B\nA: C\n")

    def test_missing_file(self):
        """Файл не существует."""
        with self.assertRaises(RepositoryError):
            load_test_repository("no_such_repo.txt")


if __name__ == "__main__":
    unittest.main()
