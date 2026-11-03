# Hotspot Article for Codex

一个面向中文热点写作的 Codex skill：从原始来源研究出发，产出可直接编辑和发布的长文、900 字以内短版，以及经过技术验证的本地配图。

[![Tests](https://github.com/haop28661-byte/codex-hotspot-article/actions/workflows/tests.yml/badge.svg)](https://github.com/haop28661-byte/codex-hotspot-article/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 简介

`hotspot-article` 不是“给一个题目就生成一篇空泛评论”的提示词。它把完整工作拆成研究、写作、审阅、标题、短版、配图和机械验收几个阶段，并要求每个关键事实都能回到真实来源。

一次完整调用会产出：

- 一份带完整来源索引和“终稿事实核对”表的 `知识库.md`
- 一份经过三轮编辑审阅的长文 `初稿.md` 与 `终稿.md`
- 一篇独立压缩、正文不超过 900 个可见字符的短版
- 5–10 张下载到本地并验证过实际像素的配图
- 一份记录来源、作者、授权状态、尺寸和图注的 `插图网址.txt`
- 一个通过确定性检查的完整交付文件夹

写作目标是普通手机读者：事实要准确，术语要解释，观点要有依据，叙事要让人读得下去。研究材料提供事实，不会直接变成官腔或媒体通稿的仿写。

## 适用场景

- 把一个正在发生的社会、科技、商业或公共事件写成便于分享的长文
- 需要可追溯来源，而不是只依赖模型记忆
- 同时需要长文、短版和本地插图素材
- 需要明确区分事实、当事方说法、媒体判断和作者推断
- 需要对配图授权状态做显式记录，而不是把“能下载”误写成“可发布”

## 环境要求

- 支持 skills 的 Codex 环境
- Python 3.10 或更高版本
- 推荐安装 [`uv`](https://github.com/astral-sh/uv)，用于固定 Python 3.12 运行验收脚本
- 可访问真实来源页面的网络环境
- 配图阶段需要图片下载、解码和视觉检查能力

验证脚本只依赖 Python 标准库。配图能力不可用时，skill 会保留已完成的文字成果并交付为“部分完成”，不会伪造图片。

## 安装

Codex 会从它支持的 skills 根目录发现 skill。仓库本身没有固定的安装盘符或工作目录，可以放在任意支持的 skills 根目录下。

### 用户级安装

适合所有项目都能调用。

Windows PowerShell：

```powershell
$skills = Join-Path $env:USERPROFILE '.codex\skills'
New-Item -ItemType Directory -Path $skills -Force
$target = Join-Path $skills 'hotspot-article'
git clone https://github.com/haop28661-byte/codex-hotspot-article.git $target
```

macOS / Linux：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/haop28661-byte/codex-hotspot-article.git ~/.codex/skills/hotspot-article
```

### 项目级安装

适合只在某一个项目里使用，也便于把技能随项目配置一起管理。

```powershell
New-Item -ItemType Directory -Path '.agents\skills' -Force
git clone https://github.com/haop28661-byte/codex-hotspot-article.git '.agents\skills\hotspot-article'
```

macOS / Linux 将路径写成 `.agents/skills/hotspot-article` 即可。

### 从其他位置链接安装

如果你想把源码库放在别处，再将它链接到 Codex 的 skills 根目录：

Windows PowerShell：

```powershell
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.codex\skills\hotspot-article" `
  -Target "D:\dev\codex-hotspot-article"
```

macOS / Linux：

```bash
ln -s /path/to/codex-hotspot-article ~/.codex/skills/hotspot-article
```

目标目录已存在时，不要直接覆盖。先备份你自己的修改，或改用另一个 skill 目录名。

## 使用方法

这个 skill 仅显式调用。新任务必须同时提供主题和正文字数范围：

```text
$hotspot-article 某地公共交通涨价；字数范围：3000-5000字
```

文章默认写入 skill 的安装文件夹，也就是包含 `SKILL.md` 的那个目录，不会自动放到当前 Codex 工作区或其他盘符。例如项目级安装在 `.agents/skills/hotspot-article` 时，默认输出结构是：

```text
.agents/
└── skills/
    └── hotspot-article/
        ├── SKILL.md
        └── 某地公共交通涨价/
```

也可以明确指定一个任意可写的位置：

```text
$hotspot-article 某地公共交通涨价；字数范围：3000-5000字；输出目录：D:\文章
```

如果只给已经完成文字的部分成果补图，显式指定原来的部分完成文件夹：

```text
$hotspot-article 继续：D:\文章\某地公共交通涨价_部分完成_20261103-1530
```

接续模式只读取你指定的那一份部分成果，保留已有正文和标题，补完图片及清单后生成新文件夹。原部分完成文件夹不会被改写。

## 输出结构

完整任务：

```text
<delivery-root>/
└── 某地公共交通涨价/
    ├── 知识库.md
    ├── 初稿.md
    ├── 终稿.md
    ├── 涨价之后，谁在承担代价——贴图900字以内版本.md
    ├── 插图网址.txt
    ├── 插图-01-公交站台.jpg
    └── ...
```

有可用成果但未满足全部要求时：

```text
<delivery-root>/
└── 某地公共交通涨价_部分完成_20261103-1530/
    ├── 交付说明.md
    ├── 知识库.md
    ├── 初稿.md
    ├── 终稿.md
    └── ...
```

`交付说明.md` 会写明已完成内容、缺失项、原因、临时工作区、下一步和版权待确认项。

## 工作流程

1. 打开真实来源，建立带稳定来源编号的知识库。
2. 找出谁受到影响、发生了什么、转折在哪里，再构建长文的故事主线。
3. 写长文初稿，并进行手机路人首读、故事与作者声音、人话与去模板化三轮审阅。
4. 正文稳定后确定长文标题，再写独立短版并确定最多 20 个可见字符的短标题。
5. 为长文选择、下载并验证 5–10 张真正有帮助的图片。
6. 记录图片作者、来源页面、直接 URL、尺寸和授权状态；技术验证不等同于版权许可。
7. 在工作区完成确定性验收和人工阅读检查，再生成单一交付文件夹。

## 验收

在仓库根目录运行单元测试：

```bash
uv run --python 3.12 python -m unittest discover -s scripts -p "test_*.py"
```

手工验证一个交付目录：

```bash
uv run --python 3.12 python scripts/validate_deliverable.py \
  "/path/to/staging" \
  --status complete \
  --min 3000 \
  --max 5000
```

部分完成目录：

```bash
uv run --python 3.12 python scripts/validate_deliverable.py \
  "/path/to/staging" \
  --status partial \
  --staging \
  --min 3000 \
  --max 5000
```

脚本负责检查正文字数、标题和文件名、交付目录内容、图片签名与尺寸、图片重复、清单一一对应、占位符和审稿痕迹等机械规则。大众可读性、故事质量、作者声音、标题兑现、事实核对和图片主体匹配仍需要人工判断。

## 图片与版权

图片验证只证明文件能够解码、尺寸达到要求且内容与正文匹配，不证明它允许公开转载。版权信息用于发布前的人工判断，不作为选图或完成状态的门槛。

- 按内容匹配、来源可追溯、实际分辨率、视觉质量和无可见水印筛选图片。
- 公共领域、开放许可或明确允许复用的图片便于发布，但并非选图前提。
- 新闻媒体和官方机构页面可以作为身份或报道来源，但其图片不自动获得转载许可。
- 未找到明确许可时，仍可使用图片，并在清单标记为 `授权状态：需人工确认`。
- 正式发布前，人工确认署名、裁剪、商业使用和二次发布要求。
- 无法验证至少 5 张图片时，文字成果仍会以“部分完成”交付。

## 目录结构

```text
codex-hotspot-article/
├── SKILL.md
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── research-protocol.md
│   ├── story-first-writing.md
│   ├── illustration-workflow.md
│   └── delivery-and-reporting.md
├── scripts/
│   ├── validate_deliverable.py
│   └── test_validate_deliverable.py
└── .github/
    └── workflows/
        └── tests.yml
```

## 更新与卸载

通过 Git 安装时，更新：

```bash
git -C /path/to/installed/hotspot-article pull --ff-only
```

卸载时，只需从对应的 skills 根目录移除你自己安装的 `hotspot-article` 文件夹。不要删除其他地方的文章成果。

## 贡献

欢迎提交事实更准确、跨平台更稳定或验证更严格的改进。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，并确保测试通过。

## 许可证

本项目使用 [MIT License](LICENSE)。
