/* Rendering libraries are pinned in vendor/versions.json. */
"use strict";

const siteRoot = new URL(document.body.dataset.root || "../", window.location.href);
const teachingRoot = new URL("teaching/", siteRoot);
const library = document.getElementById("library");
const reader = document.getElementById("reader");
const $ = (id) => document.getElementById(id);

function escapeHTML(text) {
  return text.replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
}

// Must match slugify() in scripts/build_pages.py.
function slugify(raw) {
  return raw.trim().toLocaleLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, "").replace(/\s/g, "-") || "section";
}

function sitePath(file) {
  const url = new URL(file, siteRoot);
  return decodeURIComponent(url.pathname.slice(siteRoot.pathname.length));
}

function materialPath(path) {
  const url = new URL(path, siteRoot);
  const base = new URL("materials/", siteRoot);
  if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname) || !/\.md$/i.test(url.pathname) || url.search || url.hash) {
    throw new Error("请打开 materials 文件夹中的 Markdown 文件。");
  }
  return {url, path: decodeURIComponent(url.pathname.slice(siteRoot.pathname.length))};
}

async function getText(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const error = new Error(response.status === 404 ? "文件不存在，或该讲义尚未开放。" : `文件加载失败（${response.status}）。`);
    error.status = response.status;
    throw error;
  }
  return response.text();
}

/* ---------- Catalog ---------- */

let catalogPromise;
function loadCatalog() {
  catalogPromise ||= getText(new URL("materials.json", siteRoot)).then((text) => {
    const data = JSON.parse(text);
    if (!Array.isArray(data.courses)) throw new Error("课程目录需要包含 courses 数组。");
    const notes = new Map();
    for (const course of data.courses) {
      if (!Array.isArray(course.materials)) throw new Error("每门课程需要包含 materials 章节数组。");
      course.chapters = course.materials.map((entry, index) => {
        const path = materialPath(entry.file).path;
        const open = entry.available !== false;
        const chapter = {kind: "chapter", course, entry, path, open, number: entry.number ?? index,
          title: entry.title || path.split("/").pop(), updated: entry.updated, topics: []};
        notes.set(path, chapter);
        for (const item of entry.topics || []) {
          const topicPath = sitePath(item.file);
          const topic = {kind: "topic", course, entry: item, path: topicPath, parent: chapter,
            open: (item.available ?? open) !== false, title: item.title || topicPath.split("/").pop(),
            updated: item.updated, markdown: /\.md$/i.test(topicPath)};
          chapter.topics.push(topic);
          notes.set(topicPath, topic);
        }
        return chapter;
      });
    }
    return {data, notes};
  });
  return catalogPromise;
}

// Open course notes have their own static page; anything else uses the ?note= reader.
function noteURL(path, hash = "", notes = new Map()) {
  const info = notes.get(path);
  if (info && info.open && /\.md$/i.test(path)) {
    const url = new URL("notes/" + path.replace(/^materials\//, "").replace(/\.md$/i, ".html"), teachingRoot);
    url.hash = hash;
    return url.href;
  }
  if (info && !/\.md$/i.test(path)) return new URL(path, siteRoot).href;
  const url = new URL(teachingRoot);
  url.searchParams.set("note", path);
  url.hash = hash;
  return url.href;
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function formatDate(value) {
  return value ? `更新于 ${value}` : "";
}

async function showLibrary() {
  const status = $("library-status");
  try {
    const {data, notes} = await loadCatalog();
    const list = $("materials-list");
    const groups = [];
    for (const course of data.courses) {
      const group = element("section", "course");
      group.id = course.id;
      const header = element("div", "course-header");
      header.append(element("h2", "", course.title), element("p", "", course.description || ""),
        element("span", "course-total", `${course.chapters.length} 个章节`));
      group.append(header);
      const rows = course.chapters.map((chapter) => {
        const row = element("div", chapter.open ? "material" : "material material-pending");
        const body = element("div", "material-body");
        const title = element("h3");
        if (chapter.open) {
          const link = element("a", "material-title", chapter.title);
          link.href = noteURL(chapter.path, chapter.entry.anchor || "", notes);
          title.append(link);
        } else {
          title.textContent = chapter.title;
        }
        body.append(title);
        const detailText = chapter.entry.status || chapter.entry.description;
        if (detailText) body.append(element("p", "", detailText));
        const topicRows = [];
        const openTopics = chapter.topics.filter((topic) => topic.open);
        if (chapter.open && chapter.updated) body.append(element("p", "material-date", formatDate(chapter.updated)));
        if (openTopics.length) {
          const topics = element("ul", "topics");
          topics.setAttribute("aria-label", `${chapter.title}的拓展阅读`);
          for (const topic of openTopics) {
            const item = element("li");
            const link = element("a", "", topic.title);
            link.href = noteURL(topic.path, "", notes);
            item.append(element("span", "topic-tag", topic.markdown ? "拓展" : "互动"), link);
            topics.append(item);
            topicRows.push({element: item, search: topic.title.toLocaleLowerCase()});
          }
          body.append(topics);
        }
        const actions = element("div", "material-actions");
        if (chapter.open) {
          const read = element("a", "material-action", "阅读讲义 →");
          read.href = noteURL(chapter.path, chapter.entry.anchor || "", notes);
          read.setAttribute("aria-label", `在线阅读${chapter.title}`);
          actions.append(read);
        } else {
          actions.append(element("span", "material-action", "尚未讲授"));
        }
        row.append(element("span", "material-number", `${chapter.number}.`), body, actions);
        group.append(row);
        return {element: row, topics: topicRows,
          search: `${course.title} ${chapter.title} ${chapter.entry.description || ""}`.toLocaleLowerCase()};
      });
      list.append(group);
      groups.push({element: group, rows});
    }

    let index = null;
    const results = $("search-results");
    const showHeadingMatches = async (query) => {
      results.replaceChildren();
      results.hidden = true;
      if (query.length < 2) return 0;
      try {
        index ||= JSON.parse(await getText(new URL("search-index.json", teachingRoot)));
      } catch {
        return 0;
      }
      if ($("search").value.trim().toLocaleLowerCase() !== query) return 0;
      const matches = [];
      for (const note of index.notes) {
        for (const [level, text, slug] of note.headings) {
          if (text.toLocaleLowerCase().includes(query)) matches.push({note, text, slug, level});
        }
      }
      if (!matches.length) return 0;
      results.append(element("p", "eyebrow", `讲义中的小节 · ${matches.length} 处`));
      const ul = element("ul");
      for (const match of matches.slice(0, 40)) {
        const li = element("li");
        const link = element("a", "", match.text);
        link.href = noteURL(match.note.file, match.slug, notes);
        li.append(link, element("span", "search-context", `${match.note.title}${match.note.topic ? " · 拓展阅读" : ""}`));
        ul.append(li);
      }
      results.append(ul);
      if (matches.length > 40) results.append(element("p", "muted", "只显示前 40 处，请输入更具体的关键词。"));
      results.hidden = false;
      return matches.length;
    };

    const filter = async () => {
      const query = $("search").value.trim().toLocaleLowerCase();
      let visibleCourses = 0;
      for (const group of groups) {
        let visibleRows = 0;
        for (const row of group.rows) {
          const own = row.search.includes(query);
          let topicHit = false;
          for (const topic of row.topics) {
            const hit = !query || own || topic.search.includes(query);
            topic.element.hidden = !hit;
            topicHit ||= query && topic.search.includes(query);
          }
          row.element.hidden = !(own || topicHit);
          if (!row.element.hidden) visibleRows++;
        }
        group.element.hidden = query ? visibleRows === 0 : false;
        if (!group.element.hidden) visibleCourses++;
      }
      $("count").textContent = `${visibleCourses} 门`;
      const headingHits = await showHeadingMatches(query);
      if ($("search").value.trim().toLocaleLowerCase() !== query) return;
      status.textContent = visibleCourses || headingHits ? "" : (groups.length ? "没有找到匹配的课程、章节或小节。" : "课程即将上线，敬请期待。");
      status.hidden = Boolean(visibleCourses || headingHits);
    };
    $("search").addEventListener("input", filter);
    filter();
  } catch (error) {
    status.textContent = `暂时无法加载课程目录。${error.message}`;
  }
}

/* ---------- Reader ---------- */

let markdownReady = false;
function configureMarkdown() {
  if (markdownReady) return;
  markdownReady = true;
  // Capture TeX before Markdown can interpret underscores, backslashes or HTML.
  const math = {
    name: "math", level: "inline",
    start(src) { return src.search(/\$|\\\(/); },
    tokenizer(src) {
      const opener = src.startsWith("\\(") ? "\\(" : (src.startsWith("$") && !src.startsWith("$$") ? "$" : null);
      if (!opener) return;
      const closer = opener === "$" ? "$" : "\\)";
      let end = opener.length;
      while ((end = src.indexOf(closer, end)) !== -1) {
        let slashes = 0;
        for (let i = end - 1; i >= 0 && src[i] === "\\"; i--) slashes++;
        if (slashes % 2 === 0) {
          const text = src.slice(opener.length, end);
          if (!text.trim() || text.includes("\n")) return;
          return {type: "math", raw: src.slice(0, end + closer.length), text};
        }
        end += closer.length;
      }
    },
    renderer(token) { return `<span class="math-source">${escapeHTML(token.text)}</span>`; }
  };
  const blockMath = {
    name: "blockMath", level: "block",
    start(src) { return src.search(/^ {0,3}(?:\$\$|\\\[)/m); },
    tokenizer(src) {
      const match = /^ {0,3}\$\$[ \t]*\n?([\s\S]*?)\$\$(?:[ \t]*(?:\n|$))/.exec(src) || /^ {0,3}\\\[[ \t]*\n?([\s\S]*?)\\\](?:[ \t]*(?:\n|$))/.exec(src);
      if (match) return {type: "blockMath", raw: match[0], text: match[1].trim()};
    },
    renderer(token) { return `<div class="math-source math-display">${escapeHTML(token.text)}</div>`; }
  };
  // Keep each heading's source text so anchors match the static pages and search index.
  const renderer = {
    heading(token) {
      return `<h${token.depth} data-src="${escapeHTML(token.text)}">${this.parser.parseInline(token.tokens)}</h${token.depth}>\n`;
    }
  };
  marked.use({gfm: true, extensions: [math, blockMath], renderer});
}

function resolveLinks(article, fileURL, notes) {
  const materials = new URL("materials/", siteRoot);
  for (const anchor of article.querySelectorAll("a[href]")) {
    const href = anchor.getAttribute("href");
    if (href.startsWith("#")) continue;
    const target = new URL(href, fileURL);
    const internal = target.origin === siteRoot.origin && target.pathname.startsWith(materials.pathname);
    const path = internal ? decodeURIComponent(target.pathname.slice(siteRoot.pathname.length)) : "";
    const info = notes.get(path);
    if (info && !info.open) {
      // Notes for chapters not yet taught are not published: keep the words, drop the link.
      const pending = element("span", "link-pending");
      pending.append(...anchor.childNodes);
      pending.title = "这部分讲义尚未开放";
      anchor.replaceWith(pending);
    } else if (internal && /\.md$/i.test(target.pathname)) {
      anchor.href = noteURL(path, target.hash, notes);
    } else {
      anchor.href = target.href;
      if (target.origin !== siteRoot.origin && /^https?:$/.test(target.protocol)) anchor.rel = "noopener noreferrer";
    }
  }
  for (const image of article.querySelectorAll("img[src]")) {
    image.src = new URL(image.getAttribute("src"), fileURL).href;
    // srcset may contain relative URLs; use the resolved src consistently.
    image.removeAttribute("srcset");
    image.loading = "lazy";
  }
}

function addOutline(article) {
  const used = new Set();
  const toc = $("toc");
  toc.replaceChildren();
  const entries = [];
  for (const heading of article.querySelectorAll("h1,h2,h3,h4,h5,h6")) {
    const stem = slugify(heading.dataset.src ?? heading.textContent);
    let slug = stem;
    let suffix = 1;
    while (used.has(slug)) slug = `${stem}-${suffix++}`;
    used.add(slug);
    heading.id = slug;
    heading.removeAttribute("data-src");
    if (heading.matches("h1,h2,h3")) {
      const link = element("a", `toc-${heading.localName}`);
      link.append(...heading.cloneNode(true).childNodes);
      link.href = `#${slug}`;
      toc.append(link);
      entries.push({heading, link});
    }
  }
  const outline = $("outline");
  outline.hidden = entries.length < 2;
  $("toc-toggle").hidden = outline.hidden;
  if (outline.hidden) return;

  // Highlight the section being read.
  let current = null;
  const mark = (entry) => {
    if (entry === current) return;
    current?.link.classList.remove("active");
    current?.link.removeAttribute("aria-current");
    current = entry;
    if (!entry) return;
    entry.link.classList.add("active");
    entry.link.setAttribute("aria-current", "location");
    if (!outline.classList.contains("open")) {
      const top = entry.link.offsetTop - outline.clientHeight / 3;
      if (Math.abs(outline.scrollTop - top) > outline.clientHeight / 3) outline.scrollTop = top;
    }
  };
  const update = () => {
    let active = entries[0];
    for (const entry of entries) {
      if (entry.heading.getBoundingClientRect().top - 90 <= 0) active = entry; else break;
    }
    mark(active);
  };
  let ticking = false;
  window.addEventListener("scroll", () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { ticking = false; update(); });
  }, {passive: true});
  update();

  // On narrow screens the outline opens as a panel from the toolbar button.
  const toggle = $("toc-toggle");
  const setOpen = (open) => {
    outline.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("toc-open", open);
  };
  toggle.addEventListener("click", () => setOpen(!outline.classList.contains("open")));
  toc.addEventListener("click", (event) => { if (event.target.closest("a")) setOpen(false); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") setOpen(false); });
  document.addEventListener("click", (event) => {
    if (outline.classList.contains("open") && !outline.contains(event.target) && event.target !== toggle) setOpen(false);
  });
}

function pagerLink(direction, label, title, href) {
  const link = element("a", `pager-${direction}`);
  link.href = href;
  link.append(element("span", "pager-label", label), element("span", "pager-title", title));
  return link;
}

function addPager(info, notes) {
  const pager = $("pager");
  pager.replaceChildren();
  if (!info) return;
  const chapters = info.course.chapters.filter((chapter) => chapter.open);
  let previous = null;
  let next = null;
  if (info.kind === "chapter") {
    const at = chapters.indexOf(info);
    const before = chapters[at - 1];
    const after = chapters[at + 1];
    if (before) previous = pagerLink("prev", "← 上一章", `${before.number}. ${before.title}`, noteURL(before.path, before.entry.anchor || "", notes));
    if (after) next = pagerLink("next", "下一章 →", `${after.number}. ${after.title}`, noteURL(after.path, after.entry.anchor || "", notes));
  } else {
    const parent = info.parent;
    previous = pagerLink("prev", "← 所属章节", `${parent.number}. ${parent.title}`, noteURL(parent.path, parent.entry.anchor || "", notes));
    const siblings = parent.topics.filter((topic) => topic.open);
    const after = siblings[siblings.indexOf(info) + 1];
    if (after) next = pagerLink("next", "下一篇拓展 →", after.title, noteURL(after.path, "", notes));
    else {
      const following = chapters[chapters.indexOf(parent) + 1];
      if (following) next = pagerLink("next", "下一章 →", `${following.number}. ${following.title}`, noteURL(following.path, following.entry.anchor || "", notes));
    }
  }
  if (!previous && !next) return;
  pager.append(previous || element("span"), next || element("span"));
  pager.hidden = false;
}

function noteMeta(info) {
  if (!info) return "";
  const where = info.kind === "chapter" ? `${info.course.title} · 第 ${info.number} 章` : `${info.course.title} · 第 ${info.parent.number} 章拓展阅读`;
  return [where, formatDate(info.updated)].filter(Boolean).join(" · ");
}

// Expandable derivations print in full.
window.addEventListener("beforeprint", () => {
  for (const details of document.querySelectorAll("#note details:not([open])")) {
    details.open = true;
    details.dataset.printOpened = "";
  }
});
window.addEventListener("afterprint", () => {
  for (const details of document.querySelectorAll("#note details[data-print-opened]")) {
    details.open = false;
    delete details.dataset.printOpened;
  }
});

function setupToTop() {
  const button = $("to-top");
  const update = () => { button.hidden = window.scrollY < 900; };
  window.addEventListener("scroll", update, {passive: true});
  button.addEventListener("click", () => {
    window.scrollTo({top: 0, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"});
  });
  update();
}

// Give the equation body its own scroll area; KaTeX positions tags absolutely by default.
function layoutNumberedEquations(article) {
  const scrollAreas = [];
  for (const html of article.querySelectorAll(".katex-display > .katex > .katex-html")) {
    const tag = html.querySelector(":scope > .katex-tag, :scope > .tag");
    if (!tag) continue;
    const body = element("span", "equation-body");
    for (const child of Array.from(html.childNodes)) {
      if (child !== tag) body.append(child);
    }
    const scroll = element("span", "equation-scroll");
    scroll.append(body);
    html.prepend(scroll);
    html.classList.add("numbered-equation");
    const display = html.closest(".katex-display");
    display.addEventListener("keydown", (event) => {
      if (event.target !== display || !["ArrowLeft", "ArrowRight"].includes(event.key) || scroll.scrollWidth <= scroll.clientWidth + 1) return;
      event.preventDefault();
      scroll.scrollBy({left: (event.key === "ArrowRight" ? 1 : -1) * scroll.clientWidth * .6});
    });
    scrollAreas.push({scroll, display});
  }
  const updateFocus = () => {
    for (const {scroll, display} of scrollAreas) {
      const overflows = scroll.scrollWidth > scroll.clientWidth + 1;
      if (overflows) {
        display.tabIndex = 0;
        display.setAttribute("role", "region");
        display.setAttribute("aria-label", "长公式，可左右滚动查看");
      } else {
        display.removeAttribute("tabindex");
        display.removeAttribute("role");
        display.removeAttribute("aria-label");
      }
    }
  };
  if (scrollAreas.length && window.ResizeObserver) {
    const observer = new ResizeObserver(updateFocus);
    for (const {scroll} of scrollAreas) observer.observe(scroll);
  }
  updateFocus();
  document.fonts?.ready.then(updateFocus);
}

async function showNote(requested, isStaticPage) {
  if (library) library.hidden = true;
  reader.hidden = false;
  const status = $("reader-status");
  const article = $("note");
  const showStatus = (text) => { status.textContent = text; status.hidden = !text; };
  try {
    const {url, path} = materialPath(requested);
    let notes = new Map();
    let info;
    try {
      ({notes} = await loadCatalog());
      info = notes.get(path);
    } catch {
      // The note can still be read without the catalog; only navigation is lost.
    }
    if (info && !info.open) {
      article.removeAttribute("data-prerendered");
      article.replaceChildren(element("h1", "", info.title));
      showStatus("这一讲义尚未开放，课程讲到相应章节后会在课程目录中提供阅读链接。");
      return;
    }
    // Old ?note= links for course notes move to the note's own page.
    if (!isStaticPage && info && /\.md$/i.test(path)) {
      location.replace(noteURL(path, location.hash, notes));
      return;
    }
    let markdown = await getText(url);
    // Accept an optional UTF-8 BOM and Jekyll-style metadata in existing notes.
    markdown = markdown.replace(/^﻿/, "").replace(/^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/, "");
    if (!window.marked || !window.DOMPurify || !window.katex) throw new Error("排版组件未能加载，请刷新页面重试。");
    configureMarkdown();
    article.innerHTML = DOMPurify.sanitize(marked.parse(markdown), {USE_PROFILES: {html: true}, FORBID_TAGS: ["style", "form", "input", "button"], FORBID_ATTR: ["style", "srcset"]});
    article.removeAttribute("data-prerendered");
    if (!article.querySelector("h1")) {
      const title = document.createElement("h1");
      title.textContent = path.split("/").pop().replace(/\.md$/i, "");
      article.prepend(title);
    }
    if (!isStaticPage) document.title = `${article.querySelector("h1").textContent} · phyytang`;
    resolveLinks(article, url, notes);
    let mathErrors = 0;
    for (const expression of article.querySelectorAll(".math-source")) {
      try {
        katex.render(expression.textContent, expression, {displayMode: expression.classList.contains("math-display"), throwOnError: true, trust: false, strict: "ignore", maxExpand: 1000});
      } catch (error) {
        expression.classList.add("math-error");
        expression.title = `此公式暂时无法排版：${error.message}`;
        mathErrors++;
      }
    }
    layoutNumberedEquations(article);
    addOutline(article);
    for (const table of article.querySelectorAll("table")) {
      const wrap = element("div", "table-wrap");
      wrap.tabIndex = 0;
      wrap.setAttribute("role", "region");
      wrap.setAttribute("aria-label", "可横向滚动的表格");
      table.replaceWith(wrap);
      wrap.append(table);
    }
    $("note-meta").textContent = noteMeta(info);
    $("note-meta").hidden = !info;
    addPager(info, notes);
    setupToTop();
    showStatus(mathErrors ? "部分公式使用了暂不支持的命令，已保留原始 TeX 内容。" : "");
    if (location.hash) document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView();
  } catch (error) {
    article.removeAttribute("data-prerendered");
    showStatus(`暂时无法打开讲义。${error.message}`);
  }
}

const staticNote = document.body.dataset.note;
const requested = staticNote || new URLSearchParams(location.search).get("note");
if (requested) showNote(requested, Boolean(staticNote));
else showLibrary();
