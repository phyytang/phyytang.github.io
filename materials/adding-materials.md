# Adding materials

The website reads ordinary Markdown files from this repository. You can upload notes now and organize them into courses later.

## Publish a note

1. In the GitHub repository, open the `materials` folder.
2. Choose **Add file → Upload files** to upload a `.md` file, or **Create new file** to write one online.
3. Save the change to the `main` branch.
4. Edit `materials.json` in the repository root and add an entry for the new note.

For example, a library containing two notes can use:

```json
[
  {
    "title": "My first note",
    "description": "A short description of this material.",
    "file": "materials/my-first-note.md",
    "type": "NOTE"
  },
  {
    "title": "Another note",
    "description": "More reading material.",
    "file": "materials/another-note.md",
    "type": "NOTE"
  }
]
```

Keep a comma between entries, but no comma after the last entry. Changes appear after GitHub Pages finishes publishing.

## Share a preview link

The preview link for a file called `materials/my-first-note.md` is:

```text
https://phyytang.github.io/?note=materials/my-first-note.md
```

A file does not have to appear in `materials.json` to have a preview link. That list only controls the library homepage.

For filenames with spaces or Chinese characters, use a URL-encoded path in shared links. Links created by the library do this automatically. Descriptive filenames without spaces are also convenient.

## Link notes together

Use ordinary relative Markdown links:

```markdown
[Another note](another-note.md)
[A section in that note](another-note.md#section-heading)
![A figure](images/figure.png)
[Download a handout](handout.pdf)
```

Paths are relative to the current Markdown file. Links to `.md` files within `materials/` open as previews. Images and other files open at their original locations. GitHub file links outside this website open on GitHub, where Markdown is also previewed.

## Write equations

Use `$ ... $` for inline mathematics and `$$ ... $$` for display equations, each display delimiter on its own line. Common LaTeX commands are rendered using KaTeX. LaTeX inside code blocks stays as code.

```markdown
An inline expression: $x_i^2$.

$$
\sum_{i=1}^{n}x_i^2
$$
```

KaTeX supports many mathematical commands, but does not compile complete LaTeX documents or TikZ figures. Upload a rendered image or PDF for those.

## Return to the example

Open the [Markdown preview](preview.md) to see text, equations, and a table together.
