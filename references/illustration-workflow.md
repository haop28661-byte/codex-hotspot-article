# Illustration Workflow

Illustrations support the finished long-form article. A failure in image acquisition can make the run `部分完成`; it must not erase completed text deliverables.

## Select and source

Choose 5 to 10 positions in the final article where an image materially helps the reader understand a person, object, event, document, place, or comparison. Do not add an irrelevant image to meet the count.

Select images by subject relevance, technical quality, provenance, and the absence of visible watermarks. Rights status is recorded for later human review; it is not a gate for image selection or completion. Do not reject, replace, or omit an otherwise suitable image merely because its rights are unknown, unstated, or not explicitly reusable. When no explicit license or permission is found, include the image and mark it `授权状态：需人工确认` unless the source clearly states a restriction that makes use unsuitable. Never describe copyright as cleared without supporting terms; the publication decision remains with the user.

For each position, inspect the source page for the highest available original image rather than accepting a thumbnail or search preview. Reject visible watermarks. Also reject placeholders, CAPTCHA pages, error images, misleading crops, duplicate photographs, and images whose subject or attribution is unclear.

Download accepted candidates into the run's temporary workspace. Use contiguous two-digit names with the real extension:

```text
插图-01-简短内容标签.jpg
插图-02-简短内容标签.png
```

## Verification

Before accepting an image, verify all of the following:

- The file is non-empty.
- Its signature and decoded pixels identify an actual image.
- The full image opens in a decoder.
- The visual subject matches the intended article position.
- The extension matches the detected format.
- Width and height were measured from the downloaded pixels.
- The long edge is at least 1200 pixels when a suitable source exists.
- The same photograph is not saved twice.

Never upscale an image to fabricate the 1200-pixel threshold. If only a smaller genuine original exists, use the best available version and record:

```text
分辨率说明：低于1200像素；为可获得的最佳原始版本
```

Allow up to three candidates per intended position. If a download is corrupt or not an image, remove it in the temporary workspace and try a verified backup URL. If fewer than five verified images remain, finalize the text deliverables as `部分完成` and report the actual image count.

## Placement

Only after the prose, insertion positions, downloads, and checks are complete should accepted images be placed in the delivery folder. Insert each image between complete paragraphs with blank lines around it:

```markdown
![建议图注](插图-01-简短内容标签.jpg)

*图注：建议图注*
```

Do not split a sentence, heading, quotation, list, or table with an image. Every local image must be embedded exactly once in `终稿.md`. The compact article must contain no images or captions.

Write captions as the same narrator who wrote the article. Use one or two concrete sentences to connect the visible subject to the surrounding point. Avoid news-release boilerplate, repeated source attributions, unsupported emotional interpretation, and captions that merely restate the image. Attribution and rights information belong in `插图网址.txt`, not as a formal paragraph pasted into the caption.

## Manifest

`插图网址.txt` must have exactly one entry for every delivered image and no entry without a local file:

```text
[插图 01]
本地文件名：插图-01-简短内容标签.jpg
插入位置：在“终稿中位置前的短句”之后、“终稿中位置后的短句”之前（小节标题）
建议图注：说明图片内容与正文关系的简短图注
图片尺寸：1200×800
直接图片 URL：https://example.com/image.jpg
来源页面：https://example.com/source
作者或机构：作者姓名或机构名称
授权与署名：具体授权名称及要求的署名文字
授权状态：已确认可复用 / 需人工确认
确认状态：已下载并验证
```

Use measured dimensions, the direct URL that produced the local file, and a source page that supports identity, authorship, and reuse terms when available. Do not infer a license from a host, a news article, a search result, or the absence of a copyright notice.

`确认状态：已下载并验证` describes technical verification only. A `完成` delivery can still contain images marked `授权状态：需人工确认`; report those unresolved rights explicitly.
