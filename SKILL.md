---
name: hotspot-article
description: "Produce a sourced, mobile-friendly X long-form article in an approachable and opinionated public voice, a separately titled compact article of at most 900 visible characters, and 5-10 verified local illustrations. Use only when the user explicitly invokes $hotspot-article with a topic and article-length range."
metadata:
  short-description: "Write approachable sourced public articles"
---

# Hotspot Article

## Runtime contract

- Use one of these invocation forms:
  - New task: `$hotspot-article 主题；字数范围：3000-5000字`
  - New task with a custom delivery root: `$hotspot-article 主题；字数范围：3000-5000字；输出目录：<path>`
  - Resume illustrations: `$hotspot-article 继续：<delivery-root>/<topic>_部分完成_<YYYYMMDD-HHmm>`
- Treat the directory containing this `SKILL.md` as the skill root. Resolve references and scripts relative to that directory; never assume a fixed installation path or drive. The workspace root is the root of the current Codex project. If `输出目录` is supplied, use it as the delivery root, resolving a relative path against the workspace root. Otherwise use the workspace root.
- A new task must provide both the research topic and a positive inclusive article-length range. If either is missing, ambiguous, or invalid, ask only for the missing or corrected information and stop. Do not infer either from earlier runs, folders, samples, or defaults.
- Complete the applicable research, writing, illustration, and packaging work in the same invocation. Do not ask the user to send the prompt again or split the workflow.
- Write in Chinese unless the topic explicitly requests another language.
- Derive every object, angle, title, source, claim, image, and conclusion from the current topic and current sources. A new task must not use an earlier run's article, knowledge base, sources, image files, or titles as research input. An earlier folder may be inspected only to avoid overwriting it. The sole exception is the explicit resume form below.

The article-length range applies to the `初稿.md` and `终稿.md` bodies. Count visible article-body characters: include visible heading text and punctuation; exclude the main title, all whitespace, Markdown formatting markers, image embeds, image alt text, and standalone captions. The compact body must independently be at most 900 visible characters. `scripts/validate_deliverable.py` is the deterministic authority for these counts.

## Reader and voice contract

Write for ordinary adults who encounter the article while scrolling on a phone. Assume varied ages and education, and no specialist background. The article may carry a deeper idea, but its language and structure must make the main story, stakes, and conclusion easy to grasp without rereading.

The narrator is a curious, plain-spoken companion on the reader's side: warm, observant, and willing to have opinions. It may express a clear judgment, approval, irritation, or preference when the facts support it. It is not an official spokesperson, a neutral research report, or a performer manufacturing outrage. Its dislikes are aimed at actions, evasions, costs, and abuses, never at an identity. Never invent a scene, dialogue, thought, sensory detail, personal experience, or quotation to create feeling.

Research material supplies truth; it does not supply the article's tone or sentence structure. In ordinary prose, translate laws, notices, institutional language, and media statements into the author's own clear words. Keep an exact quotation only when its wording is itself consequential, especially when legal wording determines a right, duty, exception, or liability; explain that wording immediately. The prose must still make facts, involved parties' statements, media judgments, and author inference distinguishable.

Easy reading does not mean shallow content. Use two layers:

- The scan layer is carried by the title, opening, headings, section entries and exits, and ending. It must communicate one coherent story.
- The close-read layer adds evidence, nuance, conflict, and consequence without changing the main thread.

Prefer short, clear paragraphs and concrete verbs. Introduce a necessary term where it first appears and explain it in everyday language. A sentence that needs to be reread to recover its subject, action, or consequence is an editorial defect. Avoid both officialese and empty, slang-heavy "short-video copy"; the goal is effortless comprehension with real substance.

## Stage map

Read each detailed reference when entering its stage:

| Stage | Read | Main output |
| --- | --- | --- |
| Research | [references/research-protocol.md](references/research-protocol.md) | `知识库.md` with sources and final fact ledger |
| Draft and review | [references/story-first-writing.md](references/story-first-writing.md) | `初稿.md`, public-voice review record, `终稿.md` |
| Illustrations | [references/illustration-workflow.md](references/illustration-workflow.md) | 5-10 local images and `插图网址.txt` |
| Delivery | [references/delivery-and-reporting.md](references/delivery-and-reporting.md) | Complete or partial task folder and final report |

Do not load a later-stage reference early merely to reproduce its rules from memory. Follow the linked source when that stage begins.

## Execution states and preflight

Use exactly one final state:

- `完成`: the complete task folder exists and every required check passes.
- `部分完成`: useful research, article, or verified image output exists, but one or more non-fatal requirements remain unmet.
- `阻塞`: no trustworthy dependent deliverable can be produced because a required capability is unavailable or the central claims cannot be supported without fabrication.

Before research, verify the core capabilities: source-page access rather than snippets only, file creation and enumeration, and safe temporary-directory cleanup. If source access or safe file handling is unavailable, stop and use `阻塞`.

Check image download, decoder, and visual-inspection capabilities only when illustration work begins. Do not abort text work merely because illustration capability is unavailable. Finish and package the completed text as `部分完成` if the image requirement cannot be met.

The normal success path must finish in one invocation. A partial or blocked run may stop once the missing requirement is known, but preserve its exact temporary workspace and report that path.

## Delivery lifecycle

The delivery root is the user-supplied output directory, or the current workspace root when none is supplied. It may be on any local drive or filesystem path that the task can write to safely.

1. Do all research, note-taking, review variants, staging, drafts, failed downloads, and verification work in one newly created operating-system temporary directory.
2. Assemble a `staging` child directory containing only files that may appear in the delivered task folder. The staging directory is not the delivery folder.
3. Validate staging with `scripts/validate_deliverable.py`. Create the task folder only after a complete or partial staging check passes.
4. Place every delivered file directly inside one task folder. Do not create subdirectories.
5. Run the validator again against the delivered task folder. Only then use `完成` or `部分完成`.

Derive a readable Windows-safe topic name by removing invalid characters, control characters, trailing spaces, and trailing dots; avoid reserved names such as `CON`, `PRN`, `AUX`, `NUL`, `COM1`, and `LPT1`. Keep the path practical.

- A complete run uses `<delivery-root>/<topic>/`.
- A run with useful output but unmet requirements uses `<delivery-root>/<topic>_部分完成_<YYYYMMDD-HHmm>/`.
- If a candidate path exists, use `<path>_<YYYYMMDD-HHmm>` and then `_01`, `_02`, and so on. Never overwrite or merge into an existing folder.

A complete folder contains exactly:

```text
知识库.md
初稿.md
终稿.md
<短版标题>——贴图900字以内版本.md
插图网址.txt
插图-01-…<actual-extension>
...
```

It contains 5 to 10 verified images and no extra documents, subdirectories, hidden entries, caches, logs, review records, scripts, or temporary downloads.

A partial folder is one directly visible task folder, not a parent directory of partial projects. It contains `交付说明.md` plus every deliverable that is actually complete. It may omit unfinished documents, images, or the manifest. It must not contain failed image files or entries without a local image. See [references/delivery-and-reporting.md](references/delivery-and-reporting.md) for its exact status-file fields and reporting.

The partial folder is an immutable snapshot of its invocation. The explicit resume form may copy its approved text deliverables into a new temporary workspace and continue only the unmet image work. It must not rename or modify the original partial folder.

## Resume illustrations

Use this mode only when the prompt explicitly names one existing `_部分完成_` folder as the continuation source. Do not use this mode for a different topic, a complete folder, or an unstated earlier run.

Before continuing, verify that the source folder is a valid partial delivery and contains a complete text package:

- `交付说明.md` with `主题`, `字数范围`, `状态：部分完成`, `已完成`, `未完成`, `临时工作区`, `下一步`, and `版权待确认`.
- `知识库.md`, `初稿.md`, `终稿.md`, the compact article, the `终稿事实核对` section, source index, and a Windows-safe compact title.
- The only material unmet requirement is image delivery and its manifest; if writing, evidence, title, or compact work remains unfinished, stop and explain that a new full task is required.

Run the partial validator on the named folder before copying anything. Reopen the central sources recorded in the knowledge base to confirm they remain suitable. If the sources or claims have changed materially, stop rather than silently preserving an outdated article.

Copy the approved files into a fresh temporary workspace and staging area. Preserve the long and compact prose and their approved titles unless validation finds a contradiction that requires reporting. Fill only the missing verified images and manifest entries, update the `交付说明.md` work state in the temporary copy, and run the complete staging validator. Then create a new complete task folder under the resolved delivery root; never modify, merge into, or rename the source partial folder. If fewer than five images still cannot be verified, create a new `_部分完成_<YYYYMMDD-HHmm>` folder with a fresh status file rather than adding files to the previous one.

## Research

Read [references/research-protocol.md](references/research-protocol.md) before source work. Establish the scope, open real sources, use stable source IDs, distinguish facts from claims and inference, disclose conflicts, and reopen sources supporting central claims before drafting.

`知识库.md` must contain the required research sections, a complete source index, and a `终稿事实核对` table linking consequential statements in the finished long and compact articles to source IDs. Do not leave unresolved `待补` rows in a `完成` delivery.

Use source IDs only in the knowledge base. Keep citations, review comments, status labels, placeholders, and drafting notes out of `初稿.md`, `终稿.md`, the compact article, and captions.

Treat the knowledge base as evidence to organize, not as paragraphs to reuse. Before drafting, identify the ordinary person, product, institution, place, or decision that carries the reader-facing stakes; translate the central facts into plain language; and mark any exact wording that must survive because precision changes the meaning.

## Draft and review

Read [references/story-first-writing.md](references/story-first-writing.md) before writing. Build the article from the knowledge base around one concrete story spine, one central question, and a clear human stake. Write as the narrator defined by the reader and voice contract; do not revert to official or research-report prose merely because the sources are official.

Use a provisional long-form title while drafting. Save the complete article as `初稿.md`; do not save an outline or excerpt.

Review the saved draft in three distinct passes:

1. Mobile-passerby pass: read as a tired ordinary reader who has just scrolled onto the article. Find where the click reason is weak, the opening reports background instead of entering the story, attention drops, comprehension stalls, a sentence needs rereading, the scan layer loses the thread, or a promised payoff disappears.
2. Story-and-voice editor pass: trace the central question, causal path, turns, consequences, and payoff. Check that each section adds a fact, decision, conflict, or result; that the author sounds like a specific person rather than an institution; and that opinions and feeling are grounded in the material and remain distinct from facts.
3. Plain-language pass: remove officialese, jargon without explanation, empty significance, mechanical parallelism, false progression, template transitions, rhetorical-question chains, fake intimacy, slogan endings, empty punchlines, and slang-heavy filler. Rewrite for clear subjects, actions, and consequences without changing facts or necessary qualifications.

Publish these three rounds as clearly separated user-visible progress updates. Log only substantive issues, do not repeat an issue after it has been fixed in a later pass, and for each material issue quote the current text, state the problem, and provide a usable replacement. Apply supported changes to create a complete `终稿.md`. The final draft must contain real editorial revision, but no review transcript or changelog.

## Two-title workshop

Choose the long article's publication title after its prose and three review passes have settled. Do not finalize the compact title until the compact article itself exists.

For each version, compare candidates drawn from its concrete facts, decisions, contradictions, costs, or consequences. A title must be specific to this subject, use words an ordinary reader can understand at a glance, create a real reason to continue, match the evidence, and be paid off by its own article. The reason to click should be curiosity about a real change, choice, cost, contradiction, or consequence, not a vague claim that something is shocking, hidden, or universally important. Exclude fake suspense, alarm without substance, official jargon, and claims the article cannot deliver.

The long title has no fixed character limit, but keep its decisive object and tension clear. The compact title must:

- Contain at most 20 visible Unicode code points including punctuation.
- Contain no Windows-invalid filename characters (`<>:"/\|?*` in addition to control characters).
- Contain no line break, zero-width/format character, variation selector, or trailing dot/space.
- Be used exactly in the compact Markdown H1 and the filename prefix. Rewrite an unsafe title; never substitute a sanitized filename for a different visible title.

A working short title may guide the compact rewrite. After that rewrite, finalize the short title against the actual prose and change the file if needed. Publish one `标题思考` progress update with the shortlisted titles, the selected long and compact titles, and a concrete reason for each choice. Keep this discussion in the conversation only.

## Compact article

Create a genuine compressed article, not an excerpt, a chain of retained paragraphs, or a summary with a new title pasted on. Open on one concrete tension or decision, preserve one central question, keep the decisive turn and consequence, and end on a specific payoff. Compress the reporting, not the narrator's clarity or warmth; the compact article must sound like the same author and remain effortless to follow on a phone.

The compact article must contain no images, image embeds, or standalone image captions. It must introduce no new reporting and must preserve the distinction between facts, party statements, media judgments, and author inference. Add its consequential claims to the knowledge base's final fact ledger. Count its body with the validator and keep it at or below 900 visible characters.

## Illustrations

At this stage, read [references/illustration-workflow.md](references/illustration-workflow.md) and check image download, decoding, and visual-inspection capabilities. Work only on the finished long article; do not rewrite the compact article to accommodate illustrations.

Select 5 to 10 positions where an image materially helps. Download candidates to the temporary workspace, verify the actual pixels and subject, and add only accepted files and matching manifest entries to staging. Insert each accepted image exactly once between complete paragraphs in `终稿.md`.

Write captions in the article's human voice. Keep them concrete and brief, explain how the image helps the story, and avoid news-release wording, empty exclamation, and claims that go beyond the image or article.

If fewer than five images can be verified, do not add irrelevant files. Preserve the completed text and verified images, write `交付说明.md`, and package the run as `部分完成`. If image capabilities are unavailable, use the same fallback after the text deliverables are complete.

Image technical verification does not establish publication rights. Record unresolved rights explicitly and never describe an unlicensed image as cleared.

## Final acceptance and reporting

Read [references/delivery-and-reporting.md](references/delivery-and-reporting.md) before packaging.

Prepare the complete or partial `staging` directory, then run:

```powershell
uv run --python 3.12 python "<skill-root>/scripts/validate_deliverable.py" "<temporary-workspace>/staging" --status complete --min <lower-bound> --max <upper-bound>
```

For a partial run, create `交付说明.md` first and use:

```powershell
uv run --python 3.12 python "<skill-root>/scripts/validate_deliverable.py" "<temporary-workspace>/staging" --status partial --staging --min <lower-bound> --max <upper-bound>
```

Fix every validator error. After moving the staging contents into the final task folder, run the same check without `--staging`, using explicit `--status complete` or `--status partial`.

The model must still verify the public-readability gate, story gate, title truth and payoff, the compact article's independence, the final fact ledger, image-subject matching, and rights status. For the public-readability gate, confirm that the title, opening, headings, section entries and exits, and ending preserve the main thread; that no ordinary sentence requires rereading; that necessary terms and qualifications are explained; and that the author's views and feelings are clear, grounded, and not confused with facts. These are not delegated to the script.

Use the report format in [references/delivery-and-reporting.md](references/delivery-and-reporting.md). A `完成` report includes both titles, both body counts, the compact filename, image details, abandoned candidates, rights uncertainty, and cleanup status. A `部分完成` report names the one delivered task folder, completed and missing items, the exact temporary workspace, next steps, and rights uncertainty.
