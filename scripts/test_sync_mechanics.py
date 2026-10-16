"""Checks for the file-selection and mirroring rules; no network access."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


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
        self.previous = {name: getattr(SYNC, name) for name in ("ROOT", "DESTINATION", "MANIFEST", "LOCAL_CONFIG")}
        SYNC.ROOT = self.root
        SYNC.DESTINATION = self.root / "materials" / "Mechanics"
        SYNC.MANIFEST = self.root / "scripts" / "mechanics-manifest.json"
        SYNC.LOCAL_CONFIG = self.root / ".mechanics-source.json"
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
        self.assertEqual(len(inventory), 11)  # Seven chapter files, four assets.
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
        self.assertEqual(entries[0]["file"], "materials/Mechanics/绪论.md")
        self.assertNotIn("anchor", entries[0])
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

    def test_pdf_links_follow_existing_files_for_first_four_chapters(self):
        for _, filename, _ in SYNC.CHAPTERS:
            self.put(str(Path(filename).with_suffix(".pdf")), "%PDF-1.7\nfixture\n")
        SYNC.synchronize(self.source)
        def entries():
            data = json.loads((self.root / "materials.json").read_text())
            return next(c for c in data["courses"] if c["id"] == "theoretical-mechanics")["materials"]
        for entry in entries()[:4]:
            self.assertEqual(entry["pdf"], str(Path(entry["file"]).with_suffix(".pdf")))
            self.assertTrue((self.root / entry["pdf"]).is_file())
        self.assertTrue(all("pdf" not in entry for entry in entries()[4:]))
        (self.source / "绪论.pdf").unlink()
        SYNC.synchronize(self.source)
        self.assertNotIn("pdf", entries()[0])
        self.assertTrue(all("pdf" in entry for entry in entries()[1:4]))

    def test_sync_keeps_unavailable_chapters_and_their_files(self):
        SYNC.synchronize(self.source)
        catalog_path = self.root / "materials.json"
        data = json.loads(catalog_path.read_text())
        course = next(c for c in data["courses"] if c["id"] == "theoretical-mechanics")
        for entry in course["materials"][4:]:
            entry["available"] = False
        catalog_path.write_text(json.dumps(data))
        before = {p.name: p.read_bytes() for p in SYNC.DESTINATION.glob("*.md")}
        SYNC.synchronize(self.source)
        data = json.loads(catalog_path.read_text())
        entries = next(c for c in data["courses"] if c["id"] == "theoretical-mechanics")["materials"]
        self.assertTrue(all(entry.get("available", True) for entry in entries[:4]))
        self.assertTrue(all(entry["available"] is False for entry in entries[4:]))
        self.assertEqual(before, {p.name: p.read_bytes() for p in SYNC.DESTINATION.glob("*.md")})

    def test_publish_is_scoped_and_repeatable(self):
        remote = self.base / "remote.git"
        subprocess.run(["git", "init", "--bare", "--quiet", str(remote)], check=True)
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.STDOUT, text=True)
        git("init", "--quiet", "-b", "main")
        git("config", "user.name", "Sync test")
        git("config", "user.email", "sync@example.invalid")
        git("config", "commit.gpgsign", "false")
        aliases = self.root / "materials" / "theoretical-mechanics"
        aliases.mkdir(parents=True)
        (aliases / SYNC.ALIASES[0]).write_text("placeholder")
        git("add", ".")
        git("commit", "--quiet", "-m", "Initial fixture")
        git("remote", "add", "origin", str(remote))
        git("push", "--quiet", "-u", "origin", "main")
        (self.root / "unrelated.txt").write_text("must remain staged")
        git("add", "unrelated.txt")
        with patch.object(sys, "argv", ["sync_mechanics.py", str(self.source), "--publish"]):
            SYNC.main()
        published = subprocess.check_output(["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "main"], text=True)
        self.assertIn("materials/Mechanics/", published)
        self.assertNotIn("unrelated.txt", published)
        self.assertNotIn(".mechanics-source.json", published)
        self.assertEqual(git("diff", "--cached", "--name-only").strip(), "unrelated.txt")
        head = git("rev-parse", "HEAD")
        with patch.object(sys, "argv", ["sync_mechanics.py", "--publish"]):
            SYNC.main()
        self.assertEqual(git("rev-parse", "HEAD"), head)


if __name__ == "__main__":
    unittest.main()
