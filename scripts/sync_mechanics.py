#!/usr/bin/env python3
"""Synchronize the local Mechanics teaching folder with this website."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_pages  # noqa: E402  (same folder; builds static pages after syncing)


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "materials" / "Mechanics"
MANIFEST = ROOT / "scripts" / "mechanics-manifest.json"
LOCAL_CONFIG = ROOT / ".mechanics-source.json"
EXCLUDED_DIRS = {"tmp", "__pycache__", "node_modules"}
# Never published: PDFs, Python caches, and figure sources (plot scripts, TikZ, R data).
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pdf", ".py", ".tex", ".rda"}
NOTE_SUFFIXES = {".md", ".html"}
CHAPTERS = [
    ("绪论", "绪论.md", ""),
    ("最小作用量原理", "最小作用量原理.md", "最小作用量原理"),
    ("中心力场", "中心力场.md", ""),
    ("微扰和摄动理论", "微扰和摄动理论.md", ""),
    ("刚体运动", "刚体运动.md", ""),
    ("哈密顿力学", "哈密顿力学.md", ""),
    ("无碰撞粒子体系", "无碰撞粒子体系.md", ""),
]
# Supplementary notes shown under a chapter as “拓展阅读”: chapter number -> (title, file).
# A topic follows its chapter's availability unless materials.json sets "available" on it.
TOPICS = {
    1: [("力学相似性的更多应用", "力学相似性的更多应用.md"),
        ("费马原理与引力透镜", "费马原理与引力透镜.md")],
    2: [("卫星轨道与轨道确定", "卫星轨道与轨道确定.md"),
        ("JWST 的 L2 之旅（交互页面）", "JWST的L2之旅.html"),
        ("球对称黑洞中的粒子运动", "球对称黑洞中的粒子运动.md")],
    3: [("量子谐振子与经典极限", "量子谐振子与经典极限.md"),
        ("脉冲星三体系统与层级三体问题", "脉冲星三体系统与层级三体问题.md"),
        ("对称性自发破缺", "对称性自发破缺.md"),
        ("从振子链到连续介质", "从振子链到连续介质.md")],
    4: [("欧拉角与航天器姿态控制", "欧拉角与航天器姿态控制.md")],
    5: [("KAM 定理", "KAM定理.md"),
        ("动力学系统与混沌", "动力学系统与混沌.md")],
}
REFERENCE_PATTERNS = [
    re.compile(r"\]\(\s*<([^>]+)>"),                       # [text](<path with spaces>)
    re.compile(r"\]\(\s*([^)\s]+)"),                        # [text](path) and ![alt](path)
    re.compile(r"""\b(?:src|href|poster|data)\s*=\s*["']([^"']+)["']""", re.I),
]


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def today():
    return datetime.date.today().isoformat()


def inventory(source):
    """Every candidate file in the source folder, with its SHA-256 (None for empty files)."""
    files = {}
    for base, directories, names in os.walk(source, followlinks=False):
        directories[:] = sorted(
            name for name in directories
            if name not in EXCLUDED_DIRS and not name.startswith(".")
        )
        for name in sorted(names):
            path = Path(base) / name
            if name.startswith(".") or path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            if path.is_symlink():
                raise ValueError(f"不复制符号链接，请先确认其内容：{path}")
            if path.is_file():
                relative = path.relative_to(source).as_posix()
                data = path.read_bytes()
                files[relative] = hashlib.sha256(data).hexdigest() if data else None
    return files


def references(text, note):
    """Paths (relative to the course folder) that a note links to or embeds."""
    found = set()
    base = posixpath.dirname(note)
    for pattern in REFERENCE_PATTERNS:
        for target in pattern.findall(text):
            parts = urlsplit(target.strip())
            if parts.scheme or parts.netloc or not parts.path or parts.path.startswith("/"):
                continue
            path = posixpath.normpath(posixpath.join(base, unquote(parts.path)))
            if not path.startswith("../"):
                found.add(path)
    return found


def catalog_entries(data):
    """Chapter and topic entries of the Mechanics course, creating the course if needed."""
    courses = data.setdefault("courses", [])
    course = next((item for item in courses if item.get("id") == "theoretical-mechanics"), None)
    if course is None:
        course = {"id": "theoretical-mechanics", "title": "理论力学",
                  "description": "从作用量原理到哈密顿力学，按章节展开学习。"}
        courses.append(course)
    return course


def git_date(path):
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%cs", "--", str(path)],
                             capture_output=True, text=True, check=True).stdout.strip()
        return out or None
    except (OSError, subprocess.CalledProcessError):
        return None


def synchronize(source):
    current = inventory(source)
    for title, filename, anchor in CHAPTERS:
        if filename not in current:
            raise ValueError(f"缺少章节文件：{filename}（{title}）")
    previous = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"files": {}}
    old_files = previous["files"]

    # Previous catalog settings (availability, dates) survive every sync.
    catalog_path = ROOT / "materials.json"
    data = json.loads(catalog_path.read_text()) if catalog_path.exists() else {"courses": []}
    course = catalog_entries(data)
    old_chapters = {item.get("number"): item for item in course.get("materials", [])}
    old_topics = {topic.get("file"): topic for item in course.get("materials", []) for topic in item.get("topics", [])}

    # Content digests of every note, published or not, so dates move only when text changes.
    old_notes = previous.get("notes") or old_files
    note_digests = {}

    def updated(filename, old):
        digest = current.get(filename)
        if digest is None:  # missing or empty in the source: keep what we had
            return old.get("updated") or git_date(DESTINATION / filename) or today()
        note_digests[filename] = digest
        if filename in old_notes and old_notes[filename] != digest:
            return today()
        return old.get("updated") or git_date(DESTINATION / filename) or today()

    warnings = []
    entries, published_notes = [], []
    for number, (title, filename, anchor) in enumerate(CHAPTERS):
        old = old_chapters.get(number, {})
        entry = {"number": number, "title": title, "file": "materials/Mechanics/" + filename}
        if "available" in old:
            entry["available"] = old["available"]
        if anchor:
            entry["anchor"] = anchor
        entry["updated"] = updated(filename, old)
        chapter_open = entry.get("available", True) is not False
        if chapter_open:
            published_notes.append(filename)
        topics = []
        for topic_title, topic_file in TOPICS.get(number, []):
            old_topic = old_topics.get("materials/Mechanics/" + topic_file, {})
            topic = {"title": topic_title, "file": "materials/Mechanics/" + topic_file}
            if "available" in old_topic:
                topic["available"] = old_topic["available"]
            in_source = topic_file in current
            if not in_source and not (DESTINATION / topic_file).is_file():
                warnings.append(f"拓展讲义不存在，已跳过：{topic_file}")
                continue
            if not in_source:
                warnings.append(f"拓展讲义不在源文件夹中，沿用网站中已有的副本：{topic_file}")
            topic["updated"] = updated(topic_file, old_topic)
            if topic.get("available", chapter_open) is not False:
                published_notes.append(topic_file)
            topics.append(topic)
        if topics:
            entry["topics"] = topics
        entries.append(entry)

    known = {filename for _, filename, _ in CHAPTERS} | {f for items in TOPICS.values() for _, f in items}
    for name in sorted(current):
        if "/" not in name and PurePosixPath(name).suffix.lower() in NOTE_SUFFIXES and name not in known:
            warnings.append(f"未归入课程目录、因此不发布的讲义：{name}（可在 sync_mechanics.py 的 TOPICS 中登记）")

    # Publish open notes and only the files they use.
    wanted = set()
    for note in published_notes:
        wanted.add(note)
        path = source / note if note in current else DESTINATION / note
        # Links between notes never publish a note; the catalog alone decides that.
        wanted |= {ref for ref in references(path.read_text(encoding="utf-8", errors="replace"), note)
                   if PurePosixPath(ref).suffix.lower() != ".md"}
    publish = {}
    for relative, digest in current.items():
        if relative not in wanted:
            continue
        publish[relative] = digest

    DESTINATION.mkdir(parents=True, exist_ok=True)
    changed = 0
    kept_empty = {}
    for relative, digest in publish.items():
        target = DESTINATION / relative
        if digest is None:
            # An empty source file is almost always a damaged or cloud-only copy.
            if target.is_file() and target.stat().st_size:
                kept_empty[relative] = old_files.get(relative) or hashlib.sha256(target.read_bytes()).hexdigest()
            warnings.append(f"源文件为空，未覆盖网站副本：{relative}")
            continue
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".sync-tmp")
            shutil.copyfile(source / relative, temporary)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != digest:
                temporary.unlink()
                raise ValueError(f"源文件在同步过程中变化，请重新运行：{relative}")
            os.replace(temporary, target)
            changed += 1
    managed = {relative: digest for relative, digest in publish.items() if digest is not None}
    managed.update(kept_empty)

    # Remove only previously managed files, never unrelated website files.
    removed = 0
    for relative in old_files.keys() - managed.keys():
        target = DESTINATION / relative
        if not target.resolve().is_relative_to(DESTINATION.resolve()):
            raise ValueError("同步清单中的文件路径不合法。")
        if target.is_file():
            target.unlink()
            removed += 1
    for directory in sorted((p for p in DESTINATION.rglob("*") if p.is_dir()), reverse=True):
        try:
            directory.rmdir()  # only succeeds for folders left empty
        except OSError:
            pass

    course["materials"] = entries
    write_json(catalog_path, data)
    write_json(MANIFEST, {"files": dict(sorted(managed.items())), "notes": dict(sorted(note_digests.items()))})
    build_pages.build(ROOT)

    print(f"同步完成：源文件夹 {len(current)} 个候选文件，发布 {len(managed)} 个；新增或更新 {changed} 个，移除 {removed} 个。")
    print("发布范围：开放章节及其拓展讲义，以及这些讲义实际引用的图片和动画。")
    print("不发布：PDF、作图源文件（.py/.tex/.rda）、未被引用的手绘草图、尚未讲授章节、tmp 与隐藏文件。")
    print("已重新生成静态讲义页、搜索索引和 sitemap。原始 Mechanics 文件夹未被修改。")
    for warning in warnings:
        print("提示：" + warning)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="本地 Mechanics 文件夹；首次运行后自动记住")
    parser.add_argument("--publish", action="store_true", help="同步后提交并推送到 main，触发 GitHub Pages 发布")
    args = parser.parse_args()
    if args.source:
        source = Path(args.source).expanduser().resolve()
    elif LOCAL_CONFIG.exists():
        source = Path(json.loads(LOCAL_CONFIG.read_text())["source"])
    else:
        parser.error("首次运行需要提供 Mechanics 文件夹路径。")
    if not source.is_dir() or source == DESTINATION or ROOT.is_relative_to(source):
        parser.error("请提供独立的、本地 Mechanics 源文件夹。")
    if args.publish:
        branch = subprocess.check_output(["git", "-C", str(ROOT), "branch", "--show-current"], text=True).strip()
        if branch != "main":
            parser.error("自动发布需要在 main 分支运行。")
        git("pull", "--ff-only")
    synchronize(source)
    write_json(LOCAL_CONFIG, {"source": str(source)})
    if args.publish:
        paths = ["materials/Mechanics", "materials.json",
                 "scripts/mechanics-manifest.json", *build_pages.GENERATED]
        paths = [p for p in paths if (ROOT / p).exists() or subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", "--", p], capture_output=True).returncode == 0]
        # Only commit synchronization paths; do not sweep in unrelated staged work.
        git("add", "-A", "--", *paths)
        changed = subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--quiet", "--", *paths]).returncode
        if changed == 1:
            git("commit", "--only", "-m", "Sync Mechanics teaching materials", "--", *paths)
        elif changed != 0:
            raise RuntimeError("无法检查暂存的同步文件。")
        # Buffer larger animation updates instead of using chunked HTTP uploads.
        git("-c", "http.postBuffer=524288000", "-c", "http.version=HTTP/1.1", "push", "origin", "main")
        print("已推送。GitHub Pages 完成发布后，网站将显示最新讲义。")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"同步未完成：{error}", file=sys.stderr)
        sys.exit(1)
