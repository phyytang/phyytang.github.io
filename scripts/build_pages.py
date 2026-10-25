#!/usr/bin/env python3
"""Build static reading pages, the heading search index and sitemap.xml from materials.json.

Each open Markdown note gets its own page under teaching/notes/ with a real title,
description and plain-text body, so search engines and chat-app link previews can read
it. In the browser, assets/site.js replaces that body with the fully typeset note.
Runs automatically at the end of sync_mechanics.py; can also be run on its own:

    python3 scripts/build_pages.py
"""

import datetime
import html
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://phyytang.github.io/"
TEMPLATE = Path("teaching") / "index.html"
NOTES_DIR = Path("teaching") / "notes"
INDEX = Path("teaching") / "search-index.json"
SITEMAP = Path("sitemap.xml")
COURSES_DIR = Path("teaching") / "courses"
GENERATED = [str(TEMPLATE), "index.html", str(NOTES_DIR), str(COURSES_DIR), str(INDEX), str(SITEMAP)]

HTML_BLOCK = re.compile(r"^ {0,3}</?(?:details|summary|div|table|thead|tbody|tr|td|th|p|figure|figcaption|section|aside|blockquote|ul|ol|li|center|dl|dt|dd|nav|hr|h[1-6])(?:\s|/?>|$)", re.I)
HEADING = re.compile(r"^ {0,3}(#{1,6})(?=\s|$)(.*)$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def slugify(raw):
    """Must match slugify() in assets/site.js."""
    text = raw.strip().lower()
    kept = "".join(ch for ch in text if unicodedata.category(ch)[0] in "LN" or ch in "_-" or ch.isspace())
    return re.sub(r"\s", "-", kept) or "section"


def heading_text(rest):
    """Heading text as marked's lexer reports it (closing #'s removed)."""
    text = rest.strip()
    if text.endswith("#"):
        trimmed = text.rstrip("#")
        if not trimmed or trimmed.endswith(" "):
            text = trimmed.strip()
    return text


def plain(text):
    """Readable text from inline Markdown/HTML (for titles, descriptions, the index)."""
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(\*\*|__|\*|`)", "", text)
    text = text.replace("$", "")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def strip_front_matter(markdown):
    markdown = markdown.lstrip("﻿")
    return re.sub(r"\A---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)", "", markdown)


def blocks(markdown):
    """Yield ("heading", level, raw) and ("text", lines) blocks, skipping code, math and HTML."""
    lines = markdown.splitlines()
    i, paragraph = 0, []

    def flush():
        nonlocal paragraph
        if paragraph:
            yield ("text", paragraph)
        paragraph = []

    while i < len(lines):
        line = lines[i]
        fence = FENCE.match(line)
        if fence:
            yield from flush()
            marker = fence.group(1)
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(marker[0] * len(marker)):
                i += 1
            i += 1
            continue
        stripped = line.strip()
        if stripped.startswith("$$") or stripped.startswith("\\["):
            yield from flush()
            closer = "$$" if stripped.startswith("$$") else "\\]"
            if not (len(stripped) > 2 and stripped.endswith(closer) and stripped != closer):
                i += 1
                while i < len(lines) and closer not in lines[i]:
                    i += 1
            i += 1
            continue
        if HTML_BLOCK.match(line):
            yield from flush()
            while i < len(lines) and lines[i].strip():
                i += 1
            continue
        match = HEADING.match(line)
        if match:
            yield from flush()
            yield ("heading", len(match.group(1)), heading_text(match.group(2)))
        elif not stripped:
            yield from flush()
        else:
            paragraph.append(stripped)
        i += 1
    yield from flush()


def headings_with_slugs(markdown, stem):
    found = [(level, raw) for kind, *rest in blocks(markdown) if kind == "heading" for level, raw in [rest]]
    if not any(level == 1 for level, _ in found):
        found.insert(0, (1, stem))
    used, result = set(), []
    for level, raw in found:
        base = slugify(raw)
        slug, n = base, 1
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        result.append((level, raw, slug))
    return result


def note_pages(data):
    """Open Markdown notes in catalog order, with course and position information."""
    for course in data.get("courses", []):
        for index, entry in enumerate(course.get("materials", [])):
            chapter_open = entry.get("available", True) is not False
            if chapter_open and entry.get("file", "").endswith(".md"):
                yield course, entry, entry.get("number", index), None
            for topic in entry.get("topics", []):
                if topic.get("available", chapter_open) is not False and topic.get("file", "").endswith(".md"):
                    yield course, topic, entry.get("number", index), entry


def page_path(file):
    return NOTES_DIR / (file.removeprefix("materials/").removesuffix(".md") + ".html")


def url_for(path):
    return SITE_URL + quote(path.as_posix())


def relative_prefix(path):
    return "../" * (len(path.parts) - 1)


def render_page(template, *, page, file, title, description, markdown, stem, course=None):
    root = relative_prefix(page)
    teaching = root + "teaching/"
    out = re.sub(r"<!-- library:start -->[\s\S]*?<!-- library:end -->", "", template)
    # The catalog's page-view total belongs only on the course directory.
    out = re.sub(r"<!-- catalog-counter:start -->[\s\S]*?<!-- catalog-counter:end -->", "", out)
    out = re.sub(r'(\s(?:href|src)=")\.\./', lambda m: m.group(1) + root, out)
    out = re.sub(r'(\s(?:href|src)=")\./', lambda m: m.group(1) + teaching, out)
    out = out.replace('data-root="../"', f'data-root="{root}" data-note="{html.escape(file)}"')
    out = re.sub(r"<title>[^<]*</title>", lambda _: f"<title>{html.escape(title)} · phyytang</title>", out)
    out = re.sub(r'<meta name="description" content="[^"]*">', lambda _: f'<meta name="description" content="{html.escape(description)}">', out)
    canonical = url_for(page)
    social = (f'<link rel="canonical" href="{canonical}">\n'
              f'  <meta property="og:type" content="article">\n'
              f'  <meta property="og:title" content="{html.escape(title)}">\n'
              f'  <meta property="og:description" content="{html.escape(description)}">\n'
              f'  <meta property="og:url" content="{canonical}">\n'
              f'  <meta property="og:site_name" content="phyytang · 课程与讲义">\n  ')
    out = out.replace("<title>", social + "<title>", 1)
    if course:
        back = root + course_path(course).parent.as_posix() + "/"
        out = re.sub(r'<a id="reader-back"[^>]*>[^<]*</a>',
                     lambda _: f'<a id="reader-back" href="{back}">← {html.escape(course["title"])}目录</a>', out)
    out = out.replace('<section id="reader" hidden', '<section id="reader"', 1)
    body = []
    heading_iter = iter(headings_with_slugs(markdown, stem))
    has_h1 = any(kind == "heading" and rest[0] == 1 for kind, *rest in blocks(markdown))
    if not has_h1:
        level, raw, slug = next(heading_iter)
        body.append(f'<h1 id="{html.escape(slug)}">{html.escape(plain(raw))}</h1>')
    for kind, *rest in blocks(markdown):
        if kind == "heading":
            level, raw, slug = next(heading_iter)
            body.append(f'<h{level} id="{html.escape(slug)}">{html.escape(plain(raw))}</h{level}>')
        else:
            text = plain(" ".join(line.lstrip("> -*+").strip() for line in rest[0]))
            if text:
                body.append(f"<p>{html.escape(text)}</p>")
    article = '<article id="note" class="markdown-body" aria-label="讲义正文" data-prerendered>' + "\n".join(body) + "</article>"
    out = re.sub(r'<article id="note"[^>]*></article>', lambda _: article, out, count=1)
    return out


def describe(markdown):
    for kind, *rest in blocks(markdown):
        if kind != "text":
            continue
        first = rest[0][0]
        if first.startswith((">", "!", "|", "<", "-", "*")) or first[:1].isdigit():
            continue
        text = plain(" ".join(rest[0]))
        if len(text) >= 20:
            return text[:118] + ("…" if len(text) > 118 else "")
    return ""


def course_path(course):
    identifier = course["id"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier):
        raise ValueError(f"课程 id 需使用小写字母、数字和连字符：{identifier}")
    return COURSES_DIR / identifier / "index.html"


def course_cards(courses, prefix):
    cards = []
    for course in courses:
        status = "课程讲义" if course.get("materials") else course.get("status", "内容筹备中")
        url = prefix + course_path(course).parent.as_posix() + "/"
        cards.append(f'<a class="course-card" href="{html.escape(url)}">'
                     f'<span class="eyebrow">{html.escape(status)}</span>'
                     f'<h2>{html.escape(course["title"])}</h2>'
                     f'<p>{html.escape(course.get("description", ""))}</p>'
                     '<span class="course-card-action">进入课程 →</span></a>')
    return "\n".join(cards)


def build_course_pages(root, template, data):
    courses = data.get("courses", [])
    written = set()
    for course in courses:
        page = course_path(course)
        prefix = relative_prefix(page)
        if course.get("visitCounter"):
            counter = ('<span id="teaching-visit-count" title="本课程目录页面的累计浏览次数，重复访问也会计数">'
                       f'{html.escape(course["title"])}页面访问次数：'
                       '<span id="busuanzi_value_page_pv" aria-live="polite">稍后更新…</span>'
                       '<span id="visit-count-unit" hidden> 次</span></span>')
        else:
            counter = ""
        out = re.sub(r"<!-- catalog-counter:start -->[\s\S]*?<!-- catalog-counter:end -->", lambda _: counter, template)
        out = re.sub(r'(\s(?:href|src)=")\.\./', lambda m: m.group(1) + prefix, out)
        out = re.sub(r'(\s(?:href|src)=")\./', lambda m: m.group(1) + prefix + "teaching/", out)
        out = out.replace('data-root="../"', f'class="course-page" data-root="{prefix}" data-course="{course["id"]}"')
        out = re.sub(r"<title>[^<]*</title>", lambda _: f'<title>{html.escape(course["title"])} · 课程与讲义 · phyytang</title>', out)
        description = html.escape(course.get("description", ""))
        out = re.sub(r'<meta name="description" content="[^"]*">', lambda _: f'<meta name="description" content="{description}">', out)
        canonical = SITE_URL + course_path(course).parent.as_posix() + "/"
        out = out.replace("<title>", f'<link rel="canonical" href="{canonical}">\n  <title>', 1)
        out = out.replace('<div class="hero">', f'<a class="course-back" href="{prefix}teaching/">← 全部课程</a>\n      <div class="hero">', 1)
        out = out.replace('<h1 id="library-title">课程与讲义</h1>', f'<h1 id="library-title">{html.escape(course["title"])}</h1>')
        out = re.sub(r'<p class="intro">[\s\S]*?</p>', lambda _: f'<p class="intro">{description}</p>', out, count=1)
        out = out.replace('课程目录 <span id="count"', '章节与讲义 <span id="count"')
        out = out.replace('搜索课程…', '搜索章节或小节标题…').replace('搜索课程</span>', '搜索章节或小节</span>')
        out = re.sub(r'<div id="materials-list"[^>]*>[\s\S]*?</div>', '<div id="materials-list" class="materials-list"></div>', out, count=1)
        target = root / page
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_text(encoding="utf-8") != out:
            target.write_text(out, encoding="utf-8")
        written.add(target.resolve())
    if (root / COURSES_DIR).exists():
        for stale in (root / COURSES_DIR).glob("*/index.html"):
            if stale.resolve() not in written:
                stale.unlink()
    # Keep both entry pages in sync with the same course catalog.
    cards = course_cards(courses, "../")
    hub = re.sub(r'<div id="materials-list"[^>]*>[\s\S]*?</div>',
                 lambda _: f'<div id="materials-list" class="materials-list course-grid">{cards}</div>', template, count=1)
    if (root / TEMPLATE).read_text(encoding="utf-8") != hub:
        (root / TEMPLATE).write_text(hub, encoding="utf-8")
    homepage = root / "index.html"
    if homepage.is_file():
        source = homepage.read_text(encoding="utf-8")
        home = re.sub(r'<!-- home-courses:start -->[\s\S]*?<!-- home-courses:end -->',
                      lambda _: '<!-- home-courses:start -->\n      <div class="home-course-grid">' + course_cards(courses, "") + '</div>\n      <!-- home-courses:end -->', source)
        if home != source:
            homepage.write_text(home, encoding="utf-8")


def build(root=ROOT):
    root = Path(root)
    data = json.loads((root / "materials.json").read_text(encoding="utf-8"))
    if not (root / TEMPLATE).is_file():
        print(f"提示：缺少 {TEMPLATE}，未生成静态讲义页。")
        return 0
    template = (root / TEMPLATE).read_text(encoding="utf-8")
    build_course_pages(root, template, data)
    written, index, sitemap = set(), [], [(SITE_URL, None), (SITE_URL + "teaching/", None)]
    sitemap.extend((SITE_URL + course_path(course).parent.as_posix() + "/", None) for course in data.get("courses", []))
    for course, entry, number, parent in note_pages(data):
        source = root / entry["file"]
        if not source.is_file():
            continue
        markdown = strip_front_matter(source.read_text(encoding="utf-8"))
        stem = source.stem
        found = headings_with_slugs(markdown, stem)
        h1 = next((plain(raw) for level, raw, _ in found if level == 1), stem)
        kind = f"{course.get('title', '')} · " + (f"第 {number} 章 · 拓展阅读" if parent else f"第 {number} 章")
        description = describe(markdown) or f"{kind}：{h1}"
        page = page_path(entry["file"])
        target = root / page
        target.parent.mkdir(parents=True, exist_ok=True)
        content = render_page(template, page=page, file=entry["file"], title=f"{h1} · {course.get('title', '')}",
                              description=description, markdown=markdown, stem=stem, course=course)
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            target.write_text(content, encoding="utf-8")
        written.add(target.resolve())
        index.append({
            "course": course.get("title", ""), "title": entry.get("title") or h1, "file": entry["file"],
            "chapter": number, "topic": bool(parent),
            "headings": [[level, plain(raw), slug] for level, raw, slug in found if level in (2, 3)],
        })
        sitemap.append((url_for(page), entry.get("updated")))
    notes_root = root / NOTES_DIR
    if notes_root.exists():
        for stale in notes_root.rglob("*.html"):
            if stale.resolve() not in written:
                stale.unlink()
        for directory in sorted((p for p in notes_root.rglob("*") if p.is_dir()), reverse=True):
            if not any(directory.iterdir()):
                directory.rmdir()
    index_text = json.dumps({"notes": index}, ensure_ascii=False, separators=(",", ":")) + "\n"
    index_path = root / INDEX
    if not index_path.exists() or index_path.read_text(encoding="utf-8") != index_text:
        index_path.write_text(index_text, encoding="utf-8")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in sitemap:
        lines.append(f"  <url><loc>{html.escape(loc)}</loc>" + (f"<lastmod>{lastmod}</lastmod>" if lastmod else "") + "</url>")
    lines.append("</urlset>")
    sitemap_text = "\n".join(lines) + "\n"
    sitemap_path = root / SITEMAP
    if not sitemap_path.exists() or sitemap_path.read_text(encoding="utf-8") != sitemap_text:
        sitemap_path.write_text(sitemap_text, encoding="utf-8")
    return len(index)


if __name__ == "__main__":
    try:
        count = build()
    except (OSError, ValueError, KeyError) as error:
        print(f"生成页面失败：{error}", file=sys.stderr)
        sys.exit(1)
    print(f"已生成 {count} 个静态讲义页、搜索索引和 sitemap.xml。")
