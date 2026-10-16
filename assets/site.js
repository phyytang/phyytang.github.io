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
    throw new Error("Choose a Markdown file inside the materials folder.");
  }
  return {url, path: decodeURIComponent(url.pathname.slice(siteRoot.pathname.length))};
}

async function getText(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`The file could not be loaded (${response.status}). Check that it has been uploaded and published.`);
  return response.text();
}

async function showLibrary() {
  const status = document.getElementById("library-status");
  try {
    const entries = JSON.parse(await getText(new URL("materials.json", siteRoot)));
    if (!Array.isArray(entries)) throw new Error("The materials list must be a JSON array.");
    const list = document.getElementById("materials-list");
    const rows = entries.map((entry, index) => {
      const {path} = materialPath(entry.file);
      const row = document.createElement("a");
      row.className = "material";
      row.href = noteURL(path);
      const number = document.createElement("span");
      number.className = "material-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const body = document.createElement("div");
      const type = document.createElement("span");
      type.className = "material-type";
      type.textContent = entry.type || "NOTE";
      const heading = document.createElement("h3");
      heading.textContent = entry.title || path.split("/").pop();
      const description = document.createElement("p");
      description.textContent = entry.description || "";
      body.append(type, heading, description);
      const action = document.createElement("span");
      action.className = "material-action";
      action.textContent = "Read note ↗";
      row.append(number, body, action);
      list.append(row);
      return {element: row, search: `${heading.textContent} ${description.textContent} ${type.textContent}`.toLocaleLowerCase()};
    });
    const filter = () => {
      const query = document.getElementById("search").value.trim().toLocaleLowerCase();
      let visible = 0;
      for (const row of rows) {
        row.element.hidden = !row.search.includes(query);
        if (!row.element.hidden) visible++;
      }
      document.getElementById("count").textContent = visible;
      status.textContent = visible ? "" : (entries.length ? "No materials match your search." : "No materials have been listed yet.");
      status.hidden = visible > 0;
    };
    document.getElementById("search").addEventListener("input", filter);
    filter();
  } catch (error) {
    status.textContent = `The materials list is unavailable. ${error.message}`;
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
    if (heading.matches("h2,h3")) {
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
    if (!window.marked || !window.DOMPurify || !window.katex) throw new Error("The formatting libraries could not be loaded. Try reloading this page.");
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
    let mathErrors = 0;
    for (const expression of article.querySelectorAll(".math-source")) {
      try {
        katex.render(expression.textContent, expression, {displayMode: expression.classList.contains("math-display"), throwOnError: true, trust: false, strict: "ignore", maxExpand: 1000});
      } catch (error) {
        expression.classList.add("math-error");
        expression.title = `This expression could not be rendered: ${error.message}`;
        mathErrors++;
      }
    }
    for (const table of article.querySelectorAll("table")) {
      const wrap = document.createElement("div");
      wrap.className = "table-wrap";
      wrap.tabIndex = 0;
      wrap.setAttribute("role", "region");
      wrap.setAttribute("aria-label", "Scrollable table");
      table.replaceWith(wrap);
      wrap.append(table);
    }
    source.href = `https://github.com/phyytang/phyytang.github.io/blob/main/${path.split("/").map(encodeURIComponent).join("/")}`;
    source.hidden = false;
    status.textContent = mathErrors ? "Some equations use unsupported notation and are shown as TeX." : "";
    status.hidden = mathErrors === 0;
    if (location.hash) document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView();
  } catch (error) {
    status.hidden = false;
    status.textContent = `This note could not be opened. ${error.message}`;
  }
}

const requested = new URLSearchParams(location.search).get("note");
if (requested !== null) showNote(requested);
else showLibrary();
