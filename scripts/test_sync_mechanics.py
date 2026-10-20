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
        for name in ("tmp/backup.md", "figures/tmp/old.png", ".codex_build/private.txt", "figures/__pycache__/cache.pyc", ".DS_Store", "figures/.DS_Store", "figures/cache.pyc", "lecture.pdf", "figures/appendix.PDF", "figures/notes.pDf"):
            self.put(name)
        for name in ("figures/plot.py", "figures/plot.tex", "figures/plot.png"):
            self.put(name)
        inventory = SYNC.inventory(self.source)
        self.assertEqual(len(inventory), 8)  # Seven chapter files and the image; figure sources are never candidates.
        self.assertIn("figures/plot.png", inventory)
        self.assertNotIn("figures/plot.tex", inventory)
        self.assertNotIn("figures/plot.py", inventory)
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
        self.put("绪论.md", "# 绪论\n\n![旧图](figures/old.png)\n")
        SYNC.synchronize(self.source)
        extra = SYNC.DESTINATION / "manual.txt"
        extra.write_text("not managed")
        (self.source / "figures/old.png").unlink()
        SYNC.synchronize(self.source)
        self.assertFalse((SYNC.DESTINATION / "figures/old.png").exists())
        self.assertEqual(extra.read_text(), "not managed")

    def test_sync_excludes_pdfs_and_removes_previously_managed_copies(self):
        pdf_names = [str(Path(filename).with_suffix(".pdf")) for _, filename, _ in SYNC.CHAPTERS]
        pdf_names += ["figures/appendix.PDF", "figures/notes.pDf"]
        for name in pdf_names:
            self.put(name, "%PDF-1.7\nfixture\n")
        before = {name: (self.source / name).read_bytes() for name in pdf_names}
        SYNC.synchronize(self.source)
        self.assertFalse(any(Path(name).suffix.lower() == ".pdf" for name in SYNC.inventory(self.source)))
        self.assertFalse(any(p.suffix.lower() == ".pdf" for p in SYNC.DESTINATION.rglob("*")))
        # Simulate copies managed by the old synchronization rules.
        manifest = json.loads(SYNC.MANIFEST.read_text())
        for name in pdf_names:
            target = SYNC.DESTINATION / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(before[name])
            manifest["files"][name] = "previously-managed-pdf"
        SYNC.MANIFEST.write_text(json.dumps(manifest))
        catalog_path = self.root / "materials.json"
        data = json.loads(catalog_path.read_text())
        course = next(c for c in data["courses"] if c["id"] == "theoretical-mechanics")
        course["materials"][0]["pdf"] = "materials/Mechanics/绪论.pdf"
        catalog_path.write_text(json.dumps(data))
        SYNC.synchronize(self.source)
        self.assertFalse(any(p.suffix.lower() == ".pdf" for p in SYNC.DESTINATION.rglob("*")))
        manifest = json.loads(SYNC.MANIFEST.read_text())
        self.assertTrue(all(Path(name).suffix.lower() != ".pdf" for name in manifest["files"]))
        entries = next(c for c in json.loads(catalog_path.read_text())["courses"] if c["id"] == "theoretical-mechanics")["materials"]
        self.assertTrue(all("pdf" not in entry for entry in entries))
        self.assertEqual(before, {name: (self.source / name).read_bytes() for name in pdf_names})
        SYNC.synchronize(self.source)
        self.assertFalse(any(p.suffix.lower() == ".pdf" for p in SYNC.DESTINATION.rglob("*")))

    def test_unavailable_chapters_and_their_topics_are_not_published(self):
        self.put("figures/rigid.png")
        self.put("刚体运动.md", "# 刚体运动\n\n![图](figures/rigid.png)\n")
        self.put("欧拉角与航天器姿态控制.md", "# 欧拉角\n")
        SYNC.synchronize(self.source)
        self.assertTrue((SYNC.DESTINATION / "刚体运动.md").is_file())
        self.assertTrue((SYNC.DESTINATION / "figures/rigid.png").is_file())
        catalog_path = self.root / "materials.json"
        data = json.loads(catalog_path.read_text())
        course = next(c for c in data["courses"] if c["id"] == "theoretical-mechanics")
        for entry in course["materials"][4:]:
            entry["available"] = False
        catalog_path.write_text(json.dumps(data))
        SYNC.synchronize(self.source)
        data = json.loads(catalog_path.read_text())
        entries = next(c for c in data["courses"] if c["id"] == "theoretical-mechanics")["materials"]
        self.assertTrue(all(entry.get("available", True) for entry in entries[:4]))
        self.assertTrue(all(entry["available"] is False for entry in entries[4:]))
        self.assertEqual(entries[4]["topics"][0]["file"], "materials/Mechanics/欧拉角与航天器姿态控制.md")
        for name in ("刚体运动.md", "哈密顿力学.md", "欧拉角与航天器姿态控制.md", "figures/rigid.png"):
            self.assertFalse((SYNC.DESTINATION / name).exists(), name)
        self.assertTrue((self.source / "刚体运动.md").is_file())
        # A topic can be opened on its own even while its chapter is closed.
        entries[4]["topics"][0]["available"] = True
        catalog_path.write_text(json.dumps(data))
        SYNC.synchronize(self.source)
        self.assertTrue((SYNC.DESTINATION / "欧拉角与航天器姿态控制.md").is_file())

    def test_only_referenced_assets_and_drafts_are_published(self):
        self.put("figures/used.png")
        self.put("figures/unused.png")
        self.put("figures/handdraw/used sketch.png")
        self.put("figures/handdraw/draft.png")
        self.put("中心力场.md", "# 中心力场\n\n![a](figures/used.png)\n<img src=\"./figures/handdraw/used%20sketch.png\">\n[刚体](刚体运动.md)\n")
        catalog_path = self.root / "materials.json"
        SYNC.synchronize(self.source)
        data = json.loads(catalog_path.read_text())
        course = next(c for c in data["courses"] if c["id"] == "theoretical-mechanics")
        course["materials"][4]["available"] = False
        catalog_path.write_text(json.dumps(data))
        SYNC.synchronize(self.source)
        published = {p.relative_to(SYNC.DESTINATION).as_posix() for p in SYNC.DESTINATION.rglob("*") if p.is_file()}
        self.assertIn("figures/used.png", published)
        self.assertIn("figures/handdraw/used sketch.png", published)
        self.assertNotIn("figures/unused.png", published)
        self.assertNotIn("figures/handdraw/draft.png", published)
        self.assertNotIn("刚体运动.md", published)  # linking to a closed chapter does not publish it

    def test_empty_source_file_never_replaces_a_published_copy(self):
        self.put("figures/plot.png", "picture")
        self.put("绪论.md", "# 绪论\n\n![p](figures/plot.png)\n")
        SYNC.synchronize(self.source)
        (self.source / "figures/plot.png").write_bytes(b"")
        SYNC.synchronize(self.source)
        self.assertEqual((SYNC.DESTINATION / "figures/plot.png").read_text(), "picture")
        self.assertIn("figures/plot.png", json.loads(SYNC.MANIFEST.read_text())["files"])

    def test_update_dates_follow_content_changes(self):
        SYNC.synchronize(self.source)
        def date(number):
            data = json.loads((self.root / "materials.json").read_text())
            return next(c for c in data["courses"] if c["id"] == "theoretical-mechanics")["materials"][number]["updated"]
        data = json.loads((self.root / "materials.json").read_text())
        course = next(c for c in data["courses"] if c["id"] == "theoretical-mechanics")
        course["materials"][2]["updated"] = "2000-01-01"
        course["materials"][3]["updated"] = "2000-01-01"
        (self.root / "materials.json").write_text(json.dumps(data))
        self.put("中心力场.md", "# 中心力场\n\n修改过的内容\n")
        SYNC.synchronize(self.source)
        self.assertEqual(date(2), SYNC.today())
        self.assertEqual(date(3), "2000-01-01")

    def test_publish_is_scoped_and_repeatable(self):
        remote = self.base / "remote.git"
        subprocess.run(["git", "init", "--bare", "--quiet", str(remote)], check=True)
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.STDOUT, text=True)
        git("init", "--quiet", "-b", "main")
        git("config", "user.name", "Sync test")
        git("config", "user.email", "sync@example.invalid")
        git("config", "commit.gpgsign", "false")
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
        self.assertNotIn("materials/theoretical-mechanics/", published)
        self.assertNotIn("unrelated.txt", published)
        self.assertNotIn(".mechanics-source.json", published)
        self.assertEqual(git("diff", "--cached", "--name-only").strip(), "unrelated.txt")
        head = git("rev-parse", "HEAD")
        with patch.object(sys, "argv", ["sync_mechanics.py", "--publish"]):
            SYNC.main()
        self.assertEqual(git("rev-parse", "HEAD"), head)


if __name__ == "__main__":
    unittest.main()
