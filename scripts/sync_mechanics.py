#!/usr/bin/env python3
"""Synchronize the local Mechanics teaching folder with this website."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "materials" / "Mechanics"
MANIFEST = ROOT / "scripts" / "mechanics-manifest.json"
LOCAL_CONFIG = ROOT / ".mechanics-source.json"
EXCLUDED_DIRS = {"tmp", "__pycache__", "node_modules"}
CHAPTERS = [
    ("绪论", "绪论.md", ""),
    ("最小作用量原理", "最小作用量原理.md", "最小作用量原理"),
    ("中心力场", "中心力场.md", ""),
    ("微扰和摄动理论", "微扰和摄动理论.md", ""),
    ("刚体运动", "刚体运动.md", ""),
    ("哈密顿力学", "哈密顿力学.md", ""),
    ("无碰撞粒子体系", "无碰撞粒子体系.md", ""),
]
ALIASES = [
    "00-introduction.md", "01-principle-of-least-action.md",
    "02-central-force.md", "03-perturbation-theory.md",
    "04-rigid-body-motion.md", "05-hamiltonian-mechanics.md",
    "06-collisionless-systems.md",
]


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def inventory(source):
    files = {}
    for base, directories, names in os.walk(source, followlinks=False):
        directories[:] = sorted(
            name for name in directories
            if name not in EXCLUDED_DIRS and not name.startswith(".")
        )
        for name in sorted(names):
            path = Path(base) / name
            if name.startswith(".") or path.suffix.lower() in {".pyc", ".pyo", ".pdf"}:
                continue
            if path.is_symlink():
                raise ValueError(f"不复制符号链接，请先确认其内容：{path}")
            if path.is_file():
                relative = path.relative_to(source).as_posix()
                files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def synchronize(source):
    current = inventory(source)
    for title, filename, anchor in CHAPTERS:
        if filename not in current:
            raise ValueError(f"缺少章节文件：{filename}（{title}）")
    previous = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"files": {}}
    old_files = previous["files"]
    DESTINATION.mkdir(parents=True, exist_ok=True)
    changed = 0
    for relative, digest in current.items():
        target = DESTINATION / relative
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".sync-tmp")
            shutil.copyfile(source / relative, temporary)
            if hashlib.sha256(temporary.read_bytes()).hexdigest() != digest:
                temporary.unlink()
                raise ValueError(f"源文件在同步过程中变化，请重新运行：{relative}")
            os.replace(temporary, target)
            changed += 1
    # Remove only previously managed files, never unrelated website files.
    removed = 0
    for relative in old_files.keys() - current.keys():
        target = DESTINATION / relative
        if not target.resolve().is_relative_to(DESTINATION.resolve()):
            raise ValueError("同步清单中的文件路径不合法。")
        if target.is_file():
            target.unlink()
            removed += 1
    data = json.loads((ROOT / "materials.json").read_text())
    courses = data.setdefault("courses", [])
    course = next((item for item in courses if item.get("id") == "theoretical-mechanics"), None)
    if course is None:
        course = {"id": "theoretical-mechanics", "title": "理论力学"}
        courses.append(course)
    availability = {
        item["number"]: item["available"]
        for item in course.get("materials", []) if "available" in item
    }
    entries = []
    for number, (title, filename, anchor) in enumerate(CHAPTERS):
        entry = {"number": number, "title": title, "file": "materials/Mechanics/" + filename}
        if number in availability:
            entry["available"] = availability[number]
        if anchor:
            entry["anchor"] = anchor
        entries.append(entry)
        # Keep links shared before the full notes were uploaded usable.
        alias = ROOT / "materials" / "theoretical-mechanics" / ALIASES[number]
        if alias.exists():
            relative_link = "../Mechanics/" + filename + ("#" + anchor if anchor else "")
            alias.write_text(f"# {number}. {title}\n\n本章讲义已更新：[阅读完整讲义]({relative_link})。\n")
    course["materials"] = entries
    write_json(ROOT / "materials.json", data)
    write_json(MANIFEST, {"files": dict(sorted(current.items()))})
    print(f"同步完成：共 {len(current)} 个文件，新增或更新 {changed} 个，删除已移除的文件 {removed} 个。")
    print("已排除 PDF（不区分扩展名大小写）、tmp、隐藏目录和文件、__pycache__、node_modules 及 Python 缓存。")
    print("主页七个章节的链接已更新。原始 Mechanics 文件夹未被修改。")


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
        paths = ["materials/Mechanics", "materials/theoretical-mechanics", "materials.json", "scripts/mechanics-manifest.json"]
        # Only commit synchronization paths; do not sweep in unrelated staged work.
        git("add", "--", *paths)
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
