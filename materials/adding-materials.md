# 讲义发布说明

网站按课程组织讲义。每个章节对应一个普通 Markdown 文件，点击课程目录中的章节标题，即可在线阅读。

## 更新理论力学讲义

1. 在 GitHub 仓库中打开 `materials/theoretical-mechanics/` 文件夹。
2. 找到对应章节的 `.md` 文件，点击编辑按钮。
3. 将“讲义整理中”的提示替换为正文，保留或修改章节标题。
4. 将修改提交到 `main` 分支，等待 GitHub Pages 发布。

| 章节 | Markdown 文件 |
| :--- | :--- |
| 0. 绪论 | `00-introduction.md` |
| 1. 最小作用量原理 | `01-principle-of-least-action.md` |
| 2. 中心力场 | `02-central-force.md` |
| 3. 微扰和摄动理论 | `03-perturbation-theory.md` |
| 4. 刚体运动 | `04-rigid-body-motion.md` |
| 5. 哈密顿力学 | `05-hamiltonian-mechanics.md` |
| 6. 无碰撞粒子体系 | `06-collisionless-systems.md` |

讲义更新完成后，可以删除 `materials.json` 中对应章节的 `status` 字段，或将其改为合适的提示文字。

## 添加新课程

在 `materials/` 下建立新课程的文件夹并上传 Markdown 文件，然后在根目录的 `materials.json` 中，向 `courses` 数组追加一门课程：

```json
{
  "id": "new-course",
  "title": "新课程名称",
  "description": "课程的简短介绍。",
  "materials": [
    {
      "number": 0,
      "title": "绪论",
      "file": "materials/new-course/00-introduction.md"
    }
  ]
}
```

不同课程之间用逗号分隔，最后一项后面不加逗号。`id` 应保持唯一。保存发布后，新课程会自动显示在主页，“更多课程”区域也会继续保留。

## 链接与图片

在讲义中使用相对于当前文件的路径：

```markdown
[下一章](01-principle-of-least-action.md)
[另一章的某一节](02-central-force.md#某一节的标题)
![示意图](images/figure.png)
[下载讲义](handout.pdf)
```

`materials/` 内的 Markdown 链接会打开在线阅读页面；图片和 PDF 会使用原文件。上传图片时，请保持文件夹和路径一致。

## 分享阅读链接

例如，“绪论”的阅读链接是：

```text
https://phyytang.github.io/?note=materials/theoretical-mechanics/00-introduction.md
```

Markdown 文件即使没有列入课程目录，也可以通过这样的链接打开。中文或含空格的文件名需要进行 URL 编码，主页自动生成的链接会完成编码。

## 编写数学公式

行内公式使用 `$ ... $`，独立公式使用 `$$ ... $$`。例如：

```markdown
行内公式：$x_i^2$。

$$
\sum_{i=1}^{n} x_i^2
$$
```

公式由 KaTeX 排版，代码块内的公式会保留为代码。完整 LaTeX 文档和 TikZ 图不能直接编译，可以上传对应图片或 PDF。

可以打开[中文 Markdown 排版示例](preview.md)，查看文字、公式与表格的实际效果。
