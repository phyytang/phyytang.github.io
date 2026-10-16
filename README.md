# 课程与讲义网站

网站地址：[phyytang.github.io](https://phyytang.github.io/)。

这是一个静态 GitHub Pages 网站，主页按课程列出章节，每章链接到一个 Markdown 文件并提供在线预览。目前收录“理论力学”的七个章节，正文文件暂为待更新占位页，并为以后新增课程保留空间。

## 更新讲义

编辑 `materials/theoretical-mechanics/` 下对应章节的 `.md` 文件，将占位提示替换为正文，然后提交到 `main` 分支。讲义更新后可删除 `materials.json` 中对应章节的 `status` 字段。

支持中文、图片、表格、代码块和数学公式。行内公式使用 `$ ... $`，独立公式使用 `$$ ... $$`。相对路径指向 `materials/` 内其他 Markdown 文件时，将自动打开阅读预览。

## 新增课程

在 `materials/` 下创建课程文件夹、上传讲义，再向 `materials.json` 的 `courses` 数组追加课程对象，包含唯一的 `id`、`title`、`description` 和 `materials` 章节数组。每章包含 `number`、`title`、`file`，以及可选的 `status` 或 `description`。

完整示例见[讲义发布说明](materials/adding-materials.md)。

## 网站文件

- `index.html`：中文课程目录与阅读页面。
- `materials.json`：课程和章节配置。
- `materials/`：公开的 Markdown 讲义及附件。
- `assets/`：页面样式和阅读功能。
- `vendor/`：本地托管的 Marked、DOMPurify、KaTeX 及其许可证、版本信息。

`.nojekyll` 使 Markdown 文件按原样发布，由浏览器排版。之前的 `_config.yml` 保留，但不参与当前网站构建。Markdown 中的 HTML 在显示前会经过清理；公式排版禁用受信任命令。排版组件和字体无需依赖第三方 CDN。

## 本地预览与发布

在仓库目录运行 `python3 -m http.server 8765`，然后打开 `http://localhost:8765`。直接以 `file://` 打开网页将无法读取讲义。

GitHub Pages 发布位置应为 **main / (root)**。无需安装构建工具。
