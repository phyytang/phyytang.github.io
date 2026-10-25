# phyytang.github.io

网站地址：[phyytang.github.io](https://phyytang.github.io/)。

静态 GitHub Pages 网站，由两部分组成：

- **个人学术主页**（根目录 `index.html`）：研究方向、教学、论文与联系方式。黄色虚线框标出的【…】是待填写的占位内容，发布前请补全或删除。
- **课程与讲义**（`teaching/`）：展示课程总目录，每门课程有独立页面，再列出章节和拓展讲义。目前理论力学已有讲义，计算物理和新课程预留了独立页面。

## 更新讲义

在本地原始 `Mechanics` 文件夹中编辑资料，再双击 **同步讲义.command** 或运行 `python3 scripts/sync_mechanics.py --publish`。首次运行需指定源文件夹，完整步骤见[同步说明](同步说明.md)。

同步只发布开放章节及其拓展讲义，以及这些讲义实际引用的图片和动画；PDF、作图源文件（`.py`、`.tex`、`.rda`）、未被引用的图片与手绘草图、尚未讲授的章节都留在本地。同步结束后会自动生成各课程目录、主页课程卡片、静态阅读页、搜索索引和 sitemap。源文件夹不会被改动。

支持中文、图片、表格、代码块和数学公式。行内公式使用 `$ ... $`，独立公式使用 `$$ ... $$`。讲义之间用相对链接互相引用，例如 `[“中心力场”](中心力场.md)`、`[“散射问题”](#散射问题)`；链接到尚未开放的讲义时，网页只显示文字、不显示链接。

## 课程目录配置

`materials.json` 的 `courses` 数组定义课程。每门课程包含唯一的 `id`（小写字母、数字和连字符）、`title`、`description` 与 `materials` 章节数组。空的章节数组表示课程筹备中，可设置 `status` 与 `emptyMessage` 说明进度。设置 `visitCounter: true` 可在该课程目录底部显示独立的页面访问次数。

教学总目录为 `/teaching/`，各课程目录为 `/teaching/courses/<id>/`，例如 [理论力学](https://phyytang.github.io/teaching/courses/theoretical-mechanics/) 和 [计算物理](https://phyytang.github.io/teaching/courses/computational-physics/)。添加课程配置后，运行 `python3 scripts/build_pages.py` 即可更新独立课程页、教学总目录和主页课程卡片。现有讲义地址保持不变，讲义的返回链接指向所属课程。

每章包含 `number`、`title`、`file`，以及可选字段：

- `available: false`：章节显示为“尚未讲授”，同步时不发布其正文与拓展讲义；
- `topics`：拓展讲义列表（`title`、`file`，可选 `available`）。拓展讲义默认跟随所属章节是否开放；
- `updated`：最后更新日期，由同步工具在讲义内容变化时自动填写；
- `anchor`、`status`、`description`。

理论力学的章节与拓展讲义的归属写在 `scripts/sync_mechanics.py` 的 `CHAPTERS` 与 `TOPICS` 中，开放状态保存在 `materials.json` 中。新增课程的方法见[讲义发布说明](materials/adding-materials.md)。

## 网站文件

- `index.html`：个人学术主页；旧的 `/?note=…` 分享链接会自动转到课程站。
- `teaching/index.html`：课程总目录与阅读模板；课程卡片由构建工具更新。
- `teaching/courses/<id>/index.html`：自动生成的独立课程目录，请勿手工修改。
- `teaching/notes/`、`teaching/search-index.json`、`sitemap.xml`：由 `scripts/build_pages.py` 生成，请勿手工修改。
- `materials.json`：课程、章节与拓展讲义配置。
- `materials/`：公开的 Markdown 讲义及附件；`materials/copyright.md` 是版权与使用说明（CC BY-NC-SA 4.0）。
- `assets/`：页面样式（含深色模式与打印样式）和阅读功能。
- `vendor/`：本地托管的 Marked、DOMPurify、KaTeX 及其许可证、版本信息。

`.nojekyll` 使 Markdown 文件按原样发布，由浏览器排版。Markdown 中的 HTML 在显示前会经过清理；公式排版禁用受信任命令。排版组件和字体无需依赖第三方 CDN。 JWST 独立交互页面也复用网站的 KaTeX 与自动排版扩展，并设置手机视口；长公式可横向滚动。本地直接打开该 HTML 文件时，会从正式网站读取排版资源。

## 本地预览与发布

在仓库目录运行 `python3 -m http.server 8765`，然后打开 `http://localhost:8765`（个人主页）或 `http://localhost:8765/teaching/`（课程目录）。直接以 `file://` 打开网页将无法读取讲义。

只修改了 `materials.json` 或 `teaching/index.html` 时，运行 `python3 scripts/build_pages.py` 重新生成静态讲义页。

GitHub Pages 发布位置应为 **main / (root)**。只需要 Python 3.9 或更新版本，无需安装其他构建工具。

## 访问统计

主页页脚显示“不蒜子”提供的全站累计页面浏览次数（PV）。主页、课程目录和静态讲义页都会计数，重复打开或刷新也会累计；这不是独立访客人数，也不能据此补算接入前未记录的访问量。

教学目录 `/teaching/` 的页脚另外显示“教学页面访问次数”，使用单页面浏览次数（page PV），不合并主页或各篇讲义的访问量；重复打开、刷新也会累计。该计数不显示在静态讲义页或旧版 `?note=` 阅读器中。统计使用服务已记录的数据，不能补算未记录的历史访问。

理论力学课程目录也显示独立的页面访问次数，只统计该课程主页，不合并各篇讲义或教学总目录。

统计在页面打开 20 秒后，由 `assets/visits.js` 异步加载官方脚本，仅在 `phyytang.github.io` 域名下启用，本地预览不计数。发起统计请求后，若请求失败或等待超过 10 秒会显示“暂不可用”，不会显示虚构数字；统计不可用不影响页面阅读。新增阅读页应沿用 `teaching/index.html` 模板，以保留计数接入。

## 图片排版

阅读器会自动居中独立段落或独立容器内的配图、动画和链接图片；原稿无需依赖行内居中样式。正文中的行内图片和同一容器内的并排图片不自动重排。
