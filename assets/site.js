/* Rendering libraries are pinned in vendor/versions.json. */
"use strict";

const siteRoot = new URL("./", window.location.href);
const library = document.getElementById("library");
const reader = document.getElementById("reader");

function escapeHTML(text) {
  return text.replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
}

function noteURL(path, hash = "") {
  const url = new URL(siteRoot);
  url.searchParams.set("note", path);
  url.hash = hash;
  return url.href;
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
  if (!response.ok) throw new Error(`文件加载失败（${response.status}）。请确认文件已上传并发布。`);
  return response.text();
}

async function showLibrary() {
  const status = document.getElementById("library-status");
  try {
    const data = JSON.parse(await getText(new URL("materials.json", siteRoot)));
    if (!Array.isArray(data.courses)) throw new Error("课程目录需要包含 courses 数组。");
    const list = document.getElementById("materials-list");
    const groups = [];
    for (const course of data.courses) {
      if (!Array.isArray(course.materials)) throw new Error("每门课程需要包含 materials 章节数组。");
      const group = document.createElement("section");
      group.className = "course";
      group.id = course.id;
      const header = document.createElement("div");
      header.className = "course-header";
      const heading = document.createElement("h2");
      heading.textContent = course.title;
      const description = document.createElement("p");
      description.textContent = course.description || "";
      const total = document.createElement("span");
      total.className = "course-total";
      total.textContent = `${course.materials.length} 个章节`;
      header.append(heading, description, total);
      group.append(header);
      const rows = course.materials.map((entry, index) => {
        const {path} = materialPath(entry.file);
        const available = entry.available !== false;
        const row = document.createElement(available ? "a" : "div");
        row.className = available ? "material" : "material material-pending";
        if (available) row.href = noteURL(path, entry.anchor || "");
        const number = document.createElement("span");
        number.className = "material-number";
        number.textContent = `${entry.number ?? index}.`;
        const body = document.createElement("div");
        const title = document.createElement("h3");
        title.textContent = entry.title || path.split("/").pop();
        body.append(title);
        if (entry.status || entry.description) {
          const detail = document.createElement("p");
          detail.textContent = entry.status || entry.description;
          body.append(detail);
        }
        const action = document.createElement("span");
        action.className = "material-action";
        action.textContent = available ? "阅读讲义 →" : "尚未讲授";
        row.append(number, body, action);
        group.append(row);
        return {element: row, search: `${course.title} ${entry.title} ${entry.description || ""}`.toLocaleLowerCase()};
      });
      list.append(group);
      groups.push({element: group, rows});
    }
    const filter = () => {
      const query = document.getElementById("search").value.trim().toLocaleLowerCase();
      let visibleCourses = 0;
      for (const group of groups) {
        let visibleRows = 0;
        for (const row of group.rows) {
          row.element.hidden = !row.search.includes(query);
          if (!row.element.hidden) visibleRows++;
        }
        group.element.hidden = query ? visibleRows === 0 : false;
        if (!group.element.hidden) visibleCourses++;
      }
      document.getElementById("count").textContent = `${visibleCourses} 门`;
      status.textContent = visibleCourses ? "" : (groups.length ? "没有找到匹配的课程或章节。" : "课程即将上线，敬请期待。");
      status.hidden = visibleCourses > 0;
    };
    document.getElementById("search").addEventListener("input", filter);
    filter();
  } catch (error) {
    status.textContent = `暂时无法加载课程目录。${error.message}`;
  }
}

function configureMarkdown() {
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
  marked.use({gfm: true, extensions: [math, blockMath]});
}

function resolveLinks(article, fileURL) {
  for (const anchor of article.querySelectorAll("a[href]")) {
    const href = anchor.getAttribute("href");
    if (href.startsWith("#")) continue;
    const target = new URL(href, fileURL);
    if (target.origin === siteRoot.origin && target.pathname.startsWith(new URL("materials/", siteRoot).pathname) && /\.md$/i.test(target.pathname)) {
      anchor.href = noteURL(decodeURIComponent(target.pathname.slice(siteRoot.pathname.length)), target.hash);
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
  const headings = [...article.querySelectorAll("h1,h2,h3,h4,h5,h6")];
  for (const heading of headings) {
    const stem = heading.textContent.trim().toLocaleLowerCase().replace(/[^\p{L}\p{N}_\s-]/gu, "").replace(/\s/g, "-") || "section";
    let slug = stem;
    let suffix = 1;
    while (used.has(slug)) slug = `${stem}-${suffix++}`;
    used.add(slug);
    heading.id = slug;
    if (heading.matches("h1,h2,h3")) {
      const link = document.createElement("a");
      link.href = `#${slug}`;
      link.textContent = heading.textContent;
      document.getElementById("toc").append(link);
    }
  }
  document.getElementById("outline").hidden = !document.getElementById("toc").childElementCount;
}

async function showNote(requested) {
  library.hidden = true;
  reader.hidden = false;
  const status = document.getElementById("reader-status");
  const source = document.getElementById("source-link");
  source.hidden = true;
  try {
    const {url, path} = materialPath(requested);
    let markdown = await getText(url);
    // Accept an optional UTF-8 BOM and Jekyll-style metadata in existing notes.
    markdown = markdown.replace(/^\uFEFF/, "").replace(/^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/, "");
    if (!window.marked || !window.DOMPurify || !window.katex) throw new Error("排版组件未能加载，请刷新页面重试。");
    configureMarkdown();
    const article = document.getElementById("note");
    article.innerHTML = DOMPurify.sanitize(marked.parse(markdown), {USE_PROFILES: {html: true}, FORBID_TAGS: ["style", "form", "input", "button"], FORBID_ATTR: ["style", "srcset"]});
    if (!article.querySelector("h1")) {
      const title = document.createElement("h1");
      title.textContent = path.split("/").pop().replace(/\.md$/i, "");
      article.prepend(title);
    }
    document.title = `${article.querySelector("h1").textContent} · phyytang`;
    resolveLinks(article, url);
    addOutline(article);
    if (location.hash) {
      const section = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (section?.matches("h1,h2,h3,h4,h5,h6")) document.title = `${section.textContent} · phyytang`;
    }
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
    for (const table of article.querySelectorAll("table")) {
      const wrap = document.createElement("div");
      wrap.className = "table-wrap";
      wrap.tabIndex = 0;
      wrap.setAttribute("role", "region");
      wrap.setAttribute("aria-label", "可横向滚动的表格");
      table.replaceWith(wrap);
      wrap.append(table);
    }
    source.href = `https://github.com/phyytang/phyytang.github.io/blob/main/${path.split("/").map(encodeURIComponent).join("/")}`;
    source.hidden = false;
    status.textContent = mathErrors ? "部分公式使用了暂不支持的命令，已保留原始 TeX 内容。" : "";
    status.hidden = mathErrors === 0;
    if (location.hash) document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView();
  } catch (error) {
    status.hidden = false;
    status.textContent = `暂时无法打开讲义。${error.message}`;
  }
}

const requested = new URLSearchParams(location.search).get("note");
if (requested !== null) showNote(requested);
else showLibrary();
