# Course materials website

Live site: [phyytang.github.io](https://phyytang.github.io/).

This is a static GitHub Pages website. `.nojekyll` keeps Markdown files available unchanged, and the browser renders their reading previews. The previous `_config.yml` is retained but is not used while `.nojekyll` is present.

## Add a Markdown file

1. Upload the file under `materials/`; no YAML front matter is required.
2. Add its title, description, file path, and optional type to `materials.json`.
3. Commit to `main` and wait for GitHub Pages to publish.

Example entry:

```json
{
  "title": "My note",
  "description": "A brief description.",
  "file": "materials/my-note.md",
  "type": "NOTE"
}
```

Share a reading preview using `https://phyytang.github.io/?note=materials/my-note.md`.

Relative links to other Markdown files under `materials/` are opened in the reader. Relative images and PDF links are resolved from the note's folder. External GitHub Markdown links open on GitHub. Heading anchors are derived from heading text (lowercase with spaces replaced by hyphens; repeated headings get numeric suffixes).

Use `$ ... $` for inline math and `$$ ... $$` for display equations. The two included files are examples and site instructions, not course-specific content. See [Adding materials](materials/adding-materials.md).

## Files

- `index.html`: library and reading view
- `assets/site.css`: responsive styling
- `assets/site.js`: library loading, Markdown preview, equation rendering, and relative links
- `materials.json`: list of links shown on the homepage
- `materials/`: public Markdown files and their attachments
- `vendor/`: locally hosted Marked, DOMPurify, and KaTeX, with licenses and pinned versions

Markdown HTML is sanitized before insertion; mathematical expressions render with KaTeX's `trust: false`. Rendering libraries and fonts are served by this repository, without a third-party CDN dependency.

## Local preview

Run `python3 -m http.server 8765` in the repository, then open `http://localhost:8765`. Opening `index.html` directly as a `file://` URL cannot fetch the notes.

GitHub Pages should deploy from **main / (root)** in repository Settings → Pages. No build tool or package installation is needed.
