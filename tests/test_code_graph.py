import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from code_graph.dependency_graph import build_graph
from code_graph.impact_analysis import analyze_impact
from code_graph.indexer import index_project
from code_graph.parser import parse_file, parse_python


class ParserTests(unittest.TestCase):
    def test_parse_functions(self):
        node = parse_python("def foo():\n    pass\n")
        self.assertIn("foo", node["functions"])

    def test_parse_classes(self):
        node = parse_python("class A:\n    pass\n")
        self.assertIn("A", node["classes"])

    def test_parse_imports(self):
        node = parse_python("import os\n")
        self.assertIn("os", node["imports"])

    def test_parse_import_from(self):
        node = parse_python("from pkg import mod\n")
        self.assertIn("pkg", node["imports"])

    def test_parse_calls(self):
        node = parse_python("foo()\n")
        self.assertIn("foo", node["calls"])

    def test_parse_method_call(self):
        node = parse_python("obj.run()\n")
        self.assertIn("run", node["calls"])

    def test_parse_syntax_error(self):
        node = parse_python("def foo(:\n")
        self.assertEqual(node["functions"], [])

    def test_parse_file_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.py"
            path.write_text("def x():\n    return 1\n", encoding="utf-8")
            self.assertIn("x", parse_file(path)["functions"])

    def test_parse_file_non_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.txt"
            path.write_text("hello", encoding="utf-8")
            self.assertEqual(parse_file(path)["functions"], [])

    def test_parse_empty_file(self):
        node = parse_python("")
        self.assertEqual(node["calls"], [])

    def test_parse_nested_function(self):
        node = parse_python("def a():\n    def b():\n        pass\n")
        self.assertIn("b", node["functions"])

    def test_parse_multiple_calls(self):
        node = parse_python("a()\nb()\n")
        self.assertIn("a", node["calls"])
        self.assertIn("b", node["calls"])

    def test_parse_class_method(self):
        node = parse_python("class A:\n    def m(self):\n        self.x()\n")
        self.assertIn("m", node["functions"])

    def test_parse_import_alias(self):
        node = parse_python("import os as operating\n")
        self.assertIn("os", node["imports"])

    def test_parse_no_functions(self):
        node = parse_python("x = 1\n")
        self.assertEqual(node["functions"], [])

    def test_parse_file_missing(self):
        self.assertEqual(parse_file(Path("missing.py"))["path"], "missing.py")


class GraphTests(unittest.TestCase):
    def test_build_graph_nodes(self):
        nodes = [{"path": "a.py", "imports": ["b"], "calls": []}]
        graph = build_graph(nodes)
        self.assertEqual(len(graph["nodes"]), 1)

    def test_build_graph_edges(self):
        nodes = [{"path": "a.py", "imports": ["b"], "calls": []}]
        graph = build_graph(nodes)
        self.assertEqual(graph["edges"][0]["target"], "b")

    def test_no_edges(self):
        graph = build_graph([{"path": "a.py", "imports": [], "calls": []}])
        self.assertEqual(graph["edges"], [])

    def test_edges_dedup(self):
        nodes = [{"path": "a.py", "imports": ["b", "b"], "calls": []}]
        graph = build_graph(nodes)
        self.assertEqual(len(graph["edges"]), 1)

    def test_edges_from_calls(self):
        nodes = [{"path": "a.py", "imports": [], "calls": ["foo"]}]
        graph = build_graph(nodes)
        self.assertEqual(graph["edges"][0]["target"], "foo")

    def test_edge_type(self):
        nodes = [{"path": "a.py", "imports": ["b"], "calls": []}]
        self.assertEqual(build_graph(nodes)["edges"][0]["type"], "dependency")

    def test_empty_nodes(self):
        self.assertEqual(build_graph([])["edges"], [])


class ImpactAnalysisTests(unittest.TestCase):
    def test_impact_source(self):
        graph = {"edges": [{"source": "a.py", "target": "b.py"}]}
        self.assertEqual(analyze_impact("a.py", graph), ["a.py", "b.py"])

    def test_impact_target(self):
        graph = {"edges": [{"source": "a.py", "target": "b.py"}]}
        self.assertEqual(analyze_impact("b.py", graph), ["a.py", "b.py"])

    def test_no_impact(self):
        self.assertEqual(analyze_impact("x", {"edges": []}), [])

    def test_impact_sorted(self):
        graph = {"edges": [{"source": "b.py", "target": "a.py"}]}
        self.assertEqual(analyze_impact("a.py", graph), ["a.py", "b.py"])

    def test_impact_multiple_edges(self):
        graph = {"edges": [{"source": "a", "target": "b"}, {"source": "a", "target": "c"}]}
        self.assertEqual(analyze_impact("a", graph), ["a", "b", "c"])

    def test_impact_returns_list(self):
        self.assertIsInstance(analyze_impact("x", {"edges": []}), list)


class IndexerTests(unittest.TestCase):
    def test_index_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("import b\n", encoding="utf-8")
            (root / "b.py").write_text("def b():\n    pass\n", encoding="utf-8")
            index = index_project(root)
            self.assertEqual(len(index["files"]), 2)

    def test_index_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("import b\n", encoding="utf-8")
            index = index_project(root)
            self.assertIn("graph", index)

    def test_index_skips_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "c.py").write_text("", encoding="utf-8")
            index = index_project(root)
            self.assertEqual(index["files"], [])

    def test_index_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = index_project(tmp)
            self.assertEqual(index["root"], str(tmp))

    def test_index_nested_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root / "sub"
            sub.mkdir()
            (sub / "x.py").write_text("", encoding="utf-8")
            index = index_project(root)
            self.assertEqual(len(index["files"]), 1)

    def test_index_imports_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("import b\n", encoding="utf-8")
            (root / "b.py").write_text("", encoding="utf-8")
            index = index_project(root)
            self.assertTrue(index["graph"]["edges"])

    def test_index_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(index_project(tmp)["files"], [])

    def test_index_files_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.py").write_text("", encoding="utf-8")
            self.assertIsInstance(index_project(tmp)["files"], list)

    def test_index_functions_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.py").write_text("def f():\n    pass\n", encoding="utf-8")
            index = index_project(tmp)
            self.assertIn("f", index["files"][0]["functions"])

    def test_index_classes_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.py").write_text("class A:\n    pass\n", encoding="utf-8")
            index = index_project(tmp)
            self.assertIn("A", index["files"][0]["classes"])

    def test_index_calls_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.py").write_text("foo()\n", encoding="utf-8")
            index = index_project(tmp)
            self.assertIn("foo", index["files"][0]["calls"])


if __name__ == "__main__":
    unittest.main()
