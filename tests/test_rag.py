import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from knowledge.indexer import index_project
from rag.engine import RagEngine
from vector_store.store import VectorStore, text_to_vector


class VectorStoreTests(unittest.TestCase):
    def test_search_returns_relevant_document(self):
        store = VectorStore()
        store.add("a", "ROS2 navigation stack design", {"source": "a.md"})
        store.add("b", "unrelated cooking recipe", {"source": "b.md"})
        results = store.search("ROS2 导航设计", top_k=1)
        self.assertEqual(results[0][0].id, "a")
        self.assertGreater(results[0][1], 0)

    def test_text_to_vector_is_sparse(self):
        vector = text_to_vector("hello world")
        self.assertGreater(len(vector), 0)
        self.assertLessEqual(len(vector), 512)


class KnowledgeIndexTests(unittest.TestCase):
    def test_index_project_and_retrieve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "# ROS2 Robot\n导航模块使用 Nav2 架构。", encoding="utf-8"
            )
            (root / "navigator.py").write_text(
                "class Navigator:\n    def plan_path(self): pass\n", encoding="utf-8"
            )
            subprocess.run(["git", "-C", str(root), "init", "-q"], check=False)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.name", "Test"],
                check=False,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "t@e.com"],
                check=False,
            )
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=False)
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "feat: add nav"],
                check=False,
            )

            index = index_project(root)
            engine = RagEngine(index)
            results = engine.retrieve("为什么导航这样设计？", top_k=3)
            self.assertTrue(results)
            self.assertIn("导航", " ".join(r.document.text for r in results[:1]))
            markdown = engine.evidence_markdown("导航设计", top_k=3)
            self.assertIn("# Evidence", markdown)


if __name__ == "__main__":
    unittest.main()
