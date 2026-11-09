"""Тесты построения графа зависимостей (этап 3)."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from depviz.graph import build_graph, find_cycles  # noqa: E402

LONG_CHAIN = 5000


def source(edges):
    """Сделать функцию получения зависимостей из словаря."""
    calls = []

    def get_dependencies(name):
        """Вернуть зависимости пакета и запомнить вызов."""
        calls.append(name)
        return edges.get(name, [])

    get_dependencies.calls = calls
    return get_dependencies


class BuildGraphTestCase(unittest.TestCase):
    """Обход в ширину и фильтрация."""

    def test_bfs_order(self):
        """Пакеты обходятся по уровням: сначала ближние."""
        get = source({"A": ["B", "C"], "B": ["D"], "C": ["E"], "D": []})
        graph = build_graph("A", get)
        self.assertEqual(list(graph.edges), ["A", "B", "C", "D", "E"])

    def test_transitive(self):
        """В граф попадают зависимости зависимостей."""
        graph = build_graph("A", source({"A": ["B"], "B": ["C"]}))
        self.assertEqual(graph.edges["B"], ["C"])
        self.assertEqual(graph.edges["C"], [])

    def test_each_package_requested_once(self):
        """Общая зависимость запрашивается один раз (ромб)."""
        get = source({"A": ["B", "C"], "B": ["D"], "C": ["D"]})
        build_graph("A", get)
        self.assertEqual(get.calls.count("D"), 1)

    def test_cycle_terminates(self):
        """Цикл не приводит к бесконечному обходу."""
        get = source({"A": ["B"], "B": ["C"], "C": ["A"]})
        graph = build_graph("A", get)
        self.assertEqual(sorted(graph.edges), ["A", "B", "C"])
        self.assertEqual(len(get.calls), len(graph.edges))

    def test_filter(self):
        """Пакеты с подстрокой исключаются вместе с их поддеревом."""
        get = source({"A": ["B", "XC"], "XC": ["D"], "B": []})
        graph = build_graph("A", get, "x")
        self.assertEqual(graph.edges, {"A": ["B"], "B": []})
        self.assertEqual(graph.excluded, {"XC"})
        self.assertNotIn("XC", get.calls)

    def test_root_filtered(self):
        """Если фильтр исключает корень, граф пуст."""
        graph = build_graph("A", source({"A": ["B"]}), "A")
        self.assertEqual(graph.edges, {})

    def test_no_recursion_limit(self):
        """Длинная цепочка не упирается в предел рекурсии."""
        edges = {f"P{i}": [f"P{i + 1}"] for i in range(LONG_CHAIN)}
        graph = build_graph("P0", source(edges))
        self.assertEqual(len(graph.edges), LONG_CHAIN + 1)
        self.assertEqual(find_cycles(graph), [])


class FindCyclesTestCase(unittest.TestCase):
    """Поиск циклических зависимостей."""

    def cycles(self, edges):
        """Построить граф от A и вернуть найденные циклы."""
        return find_cycles(build_graph("A", source(edges)))

    def test_no_cycles(self):
        """Ромб — не цикл."""
        edges = {"A": ["B", "C"], "B": ["D"], "C": ["D"]}
        self.assertEqual(self.cycles(edges), [])

    def test_simple_cycle(self):
        """Цикл из трёх пакетов."""
        edges = {"A": ["B"], "B": ["C"], "C": ["A"]}
        self.assertEqual(self.cycles(edges), [("A", "B", "C", "A")])

    def test_self_cycle(self):
        """Пакет зависит сам от себя."""
        self.assertEqual(self.cycles({"A": ["A"]}), [("A", "A")])

    def test_cycle_not_through_root(self):
        """Цикл глубже корня записывается начиная с наименьшего имени."""
        edges = {"A": ["C"], "C": ["B"], "B": ["C"]}
        self.assertEqual(self.cycles(edges), [("B", "C", "B")])

    def test_several_cycles(self):
        """Несколько независимых циклов."""
        edges = {"A": ["B", "D"], "B": ["A"], "D": ["E"], "E": ["D"]}
        self.assertEqual(len(self.cycles(edges)), 2)


if __name__ == "__main__":
    unittest.main()
