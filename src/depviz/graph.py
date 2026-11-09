"""Построение графа зависимостей обходом в ширину (BFS) без рекурсии."""

from collections import deque
from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    """Граф зависимостей: для каждого пакета — список его зависимостей.

    Порядок ключей ``edges`` совпадает с порядком обхода BFS.
    ``excluded`` — пакеты, пропущенные из-за подстроки фильтрации.
    """

    root: str
    edges: dict = field(default_factory=dict)
    excluded: set = field(default_factory=set)


def is_excluded(name, substring):
    """Пакет исключается, если его имя содержит подстроку (без регистра)."""
    return bool(substring) and substring.lower() in name.lower()


def build_graph(root, get_dependencies, substring=""):
    """Построить граф от пакета root обходом в ширину.

    get_dependencies(name) возвращает список имён прямых зависимостей.
    Каждый пакет запрашивается один раз, поэтому циклические
    зависимости не приводят к бесконечному обходу.
    """
    graph = DependencyGraph(root)
    if is_excluded(root, substring):
        graph.excluded.add(root)
        return graph
    discovered = {root}
    queue = deque([root])
    while queue:
        package = queue.popleft()
        kept = []
        for dep in get_dependencies(package):
            if is_excluded(dep, substring):
                graph.excluded.add(dep)
                continue
            kept.append(dep)
            if dep not in discovered:
                discovered.add(dep)
                queue.append(dep)
        graph.edges[package] = kept
    return graph


def canonical_cycle(cycle):
    """Повернуть цикл так, чтобы он начинался с наименьшего имени."""
    body = cycle[:-1]
    start = body.index(min(body))
    rotated = body[start:] + body[:start]
    return tuple(rotated + [rotated[0]])


def find_cycles(graph):
    """Найти циклы обходом в глубину на явном стеке (без рекурсии)."""
    cycles = []
    if graph.root not in graph.edges:
        return cycles
    stack = [(graph.root, iter(graph.edges[graph.root]))]
    path, on_path, finished = [graph.root], {graph.root}, set()
    while stack:
        package, children = stack[-1]
        child = next(children, None)
        if child is None:
            stack.pop()
            on_path.discard(path.pop())
            finished.add(package)
        elif child in on_path:
            cycle = canonical_cycle(path[path.index(child):] + [child])
            if cycle not in cycles:
                cycles.append(cycle)
        elif child not in finished:
            stack.append((child, iter(graph.edges.get(child, []))))
            path.append(child)
            on_path.add(child)
    return cycles
