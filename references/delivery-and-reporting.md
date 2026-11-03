# Delivery and Reporting

Use this reference when entering final acceptance and preparing the user-facing report.

## Delivery folder rules

The delivery root is the user-supplied output directory or the active Codex project root when no output directory is supplied. This rule is identical for a globally installed skill and a project-installed skill; output must not go inside the skill package directory. A project-installed skill under `<project>/.agents/skills/hotspot-article` can derive its project root as `<project>`. A globally installed skill must use the active Codex project workspace, not the terminal's current directory. Resolve a relative output directory against the active project root. If the active project root is unavailable or ambiguous, ask the user for the project folder or a custom output directory rather than falling back to a drive root, the user home directory, or an unrelated shell working directory. Everything is stored directly under that resolved root. One run produces one task folder with no subdirectories.

- Complete: `<delivery-root>/<topic>/`
- Partial: `<delivery-root>/<topic>_部分完成_<YYYYMMDD-HHmm>/`
- If a candidate path exists, append `_<YYYYMMDD-HHmm>` and then `_01`, `_02`, and so on. Never overwrite or merge into an existing folder.

Sanitize the topic portion for Windows. Remove invalid characters, control characters, trailing spaces, and trailing dots. Avoid reserved names such as `CON`, `PRN`, `AUX`, `NUL`, `COM1`, and `LPT1`. Keep the path practical and preserve the timestamp when truncating a long name.

All research, drafts, review variants, failed downloads, caches, and verification artifacts stay in one temporary workspace until packaging. A later invocation may inspect an earlier run only to avoid overwriting a folder; it must not use that run's content as research input.

## Complete package

A complete task folder contains exactly:

```text
知识库.md
初稿.md
终稿.md
<短版标题>——贴图900字以内版本.md
插图网址.txt
插图-01-…<actual-extension>
...
```

It contains 5 to 10 verified images, no `交付说明.md`, and no hidden entries, subdirectories, logs, scripts, review records, or temporary files.

Before creating the complete folder, run:

```powershell
uv run --python 3.12 python "<skill-root>/scripts/validate_deliverable.py" "<temporary-workspace>/staging" --status complete --min <lower-bound> --max <upper-bound>
```

All failures must be fixed. Then package the exact validated files and run the checker again on the complete folder. If the second check fails, do not report `完成`; when usable output remains, rename or repackage the single task folder with `_部分完成_<YYYYMMDD-HHmm>`, add the required status file, and validate it as partial.

## Partial package

A partial task folder is a visible snapshot of useful completed work, not a failed attempt hidden in the temporary directory. It must:

- Be named with `_部分完成_<YYYYMMDD-HHmm>`.
- Contain `交付说明.md`.
- Keep all completed documents and verified images directly inside the folder.
- Include `插图网址.txt` only for images that were actually delivered.
- Contain no subdirectories.

`交付说明.md` must state:

```text
主题：本任务主题
字数范围：3000-5000字
状态：部分完成
已完成：逐项列出
未完成：逐项列出并说明具体原因
临时工作区：绝对路径
下一步：具体需要补齐或重新执行的事项
版权待确认：无，或列出具体文件
```

Run the checker before moving the partial snapshot:

```powershell
uv run --python 3.12 python "<skill-root>/scripts/validate_deliverable.py" "<temporary-workspace>/staging" --status partial --staging --min <lower-bound> --max <upper-bound>
```

The partial folder remains a snapshot. A later invocation starts from current sources and creates a new complete folder rather than renaming the partial result into a claim of completion.

## Resume illustrations

An explicit prompt such as `$hotspot-article 继续：<delivery-root>/<topic>_部分完成_<YYYYMMDD-HHmm>` may copy that one partial folder's completed text into a fresh temporary workspace. Validate the partial source first, reopen its central sources, preserve its approved prose and titles, and complete only the unmet image and manifest work. Create a new complete task folder and leave the source partial unchanged.

If the source lacks a complete text package, carries a non-image unmet requirement, has changed evidence, or is missing required status fields, stop and explain the precise blocker. A repeated failure produces a new partial folder with a fresh timestamp.

## Acceptance

The checker covers deterministic requirements:

- The first Markdown title and compact filename.
- The compact title's 20-character limit and Windows-safe characters.
- Visible-body counts for the draft, final article, and compact article.
- Required document presence and folder contents.
- Image signatures, dimensions, naming, duplicates, and the 1200-pixel rule.
- Manifest fields and one-to-one matches among files, embeds, and entries.
- Source-ID, placeholder, and review-artifact leakage in publishable articles.

The model must still verify what code cannot:

- The public-readability gate: the title, opening, headings, section entries and exits, and ending preserve one understandable main thread; ordinary sentences do not require rereading; necessary terms and limits are explained.
- The author-voice gate: the narrator sounds like one specific, grounded person rather than an institution; opinions and feeling are clear, supported by the material, and not presented as facts.
- The final article's story gate.
- Whether the compact article is a genuine rewrite.
- Whether titles are specific, honest, and paid off by their articles.
- Whether the fact ledger supports every consequential statement.
- Whether official, legal, institutional, and media material has been translated into the author's words without losing necessary wording, qualifications, or uncertainty.
- Whether each image depicts the intended subject.
- Whether the final answer states rights uncertainty accurately.

## Reports

For `完成`, report:

- `完成`
- Long-form title and visible-body character count
- Compact title, filename, and visible-body character count
- Downloaded image count
- Every image filename and measured dimensions
- Number of abandoned candidates that could not be downloaded or validated
- Copyright issues requiring human confirmation, or `仍需人工确认的版权问题：无`
- Temporary-workspace cleanup status; disclose its exact path if cleanup failed

Do not add research summaries, article excerpts, review commentary, or generic closing text.

For `部分完成`, report:

- `部分完成`
- Exact delivery-folder path
- Completed outputs
- Unmet requirements and concrete reasons
- Exact temporary-workspace path
- Next steps
- Copyright issues requiring human confirmation

For a resumed task that reaches `完成`, distinguish that the result was completed from the named partial source and state that the original partial folder remains unchanged.

For `阻塞`, report the exact blocker and exact temporary path if a workspace exists. Do not create an article folder when no useful deliverable can be provided. Never claim completion when the required checks have not passed.
