"""Checks for the file-selection and mirroring rules; no network access."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("sync_mechanics", Path(__file__).with_name("sync_mechanics.py"))
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


class SyncMechanicsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.source.mkdir()
        self.root = self.base / "site"
        (self.root / "scripts").mkdir(parents=True)
        (self.root / "materials.json").write_text(json.dumps({"courses": [{"id": "other", "title": "其他课程", "materials": []}]}))
        self.previous = {name: getattr(SYNC, name) for name in ("ROOT", "DESTINATION", "MANIFEST")}
        SYNC.ROOT = self.root
        SYNC.DESTINATION = self.root / "materials" / "Mechanics"
        SYNC.MANIFEST = self.root / "scripts" / "mechanics-manifest.json"
        for _, filename, _ in SYNC.CHAPTERS:
            (self.source / filename).write_text("# 原始讲义\n\n$x_i$\n")

    def tearDown(self):
        for name, value in self.previous.items():
            setattr(SYNC, name, value)
        self.temp.cleanup()

    def put(self, name, content="data"):
        target = self.source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def test_exclusions_and_teaching_sources(self):
        for name in ("tmp/backup.md", "figures/tmp/old.png", ".codex_build/private.txt", "figures/__pycache__/cache.pyc", ".DS_Store", "figures/.DS_Store", "figures/cache.pyc"):
            self.put(name)
        for name in ("figures/plot.py", "figures/plot.tex", "figures/plot.png", "lecture.pdf"):
            self.put(name)
        inventory = SYNC.inventory(self.source)
        self.assertEqual(len(inventory), 10)  # Six distinct chapter files, four assets.
        self.assertIn("figures/plot.tex", inventory)
        self.assertFalse(any("tmp" in Path(name).parts or any(part.startswith(".") for part in Path(name).parts) for name in inventory))

    def test_links_source_integrity_and_repeatability(self):
        before = SYNC.inventory(self.source)
        SYNC.synchronize(self.source)
        self.assertEqual(before, SYNC.inventory(self.source))
        courses = json.loads((self.root / "materials.json").read_text())["courses"]
        self.assertEqual(courses[0]["id"], "other")
        entries = courses[1]["materials"]
        self.assertEqual(len(entries), 7)
        self.assertEqual(entries[0]["anchor"], "绪论")
        self.assertEqual(entries[1]["anchor"], "最小作用量原理")
        self.assertTrue(all((self.root / item["file"]).is_file() for item in entries))
        first_manifest = SYNC.MANIFEST.read_bytes()
        SYNC.synchronize(self.source)
        self.assertEqual(first_manifest, SYNC.MANIFEST.read_bytes())

    def test_removes_only_previously_managed_files(self):
        self.put("figures/old.png")
        SYNC.synchronize(self.source)
        extra = SYNC.DESTINATION / "manual.txt"
        extra.write_text("not managed")
        (self.source / "figures/old.png").unlink()
        SYNC.synchronize(self.source)
        self.assertFalse((SYNC.DESTINATION / "figures/old.png").exists())
        self.assertEqual(extra.read_text(), "not managed")


if __name__ == "__main__":
    unittest.main()
