#!/usr/bin/env python3
"""Validate deterministic hotspot-article delivery requirements."""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


COMPACT_SUFFIX = "——贴图900字以内版本.md"
STATUS_FILE = "交付说明.md"
STATUS_FIELDS = (
    "主题",
    "字数范围",
    "状态",
    "已完成",
    "未完成",
    "临时工作区",
    "下一步",
    "版权待确认",
)
BASE_DOCS = {"知识库.md", "初稿.md", "终稿.md", "插图网址.txt"}
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
CAPTION_RE = re.compile(r"^\s*\*图注[：:].*\*\s*$")
H1_RE = re.compile(r"^#(?!#)\s+(.+?)\s*$")
SOURCE_ID_RE = re.compile(r"\[S\d{2,}\]")
IMAGE_NAME_RE = re.compile(
    r"^插图-(\d{2})-[^<>:\"/\\|?*\x00-\x1f]+\.(jpg|jpeg|png|webp|gif|bmp)$",
    re.IGNORECASE,
)
MANIFEST_HEADER_RE = re.compile(r"^\[插图 (\d{2})\]$")
MANIFEST_FIELDS = {
    "本地文件名",
    "插入位置",
    "建议图注",
    "图片尺寸",
    "直接图片 URL",
    "来源页面",
    "作者或机构",
    "授权与署名",
    "授权状态",
    "确认状态",
}
INVALID_FILENAME_CHARS = set('<>:"/\\|?*')
EDITOR_ARTIFACT_RE = re.compile(
    r"^\s*(?:TODO|待补|审稿意见|编辑备注|insert here|placeholder)\s*[:：]",
    re.IGNORECASE,
)


@dataclass
class Result:
    status: str = "complete"
    folder: Path | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def detail(self, message: str) -> None:
        self.details.append(message)


def read_utf8(path: Path, result: Result) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        result.error(f"{path.name}: not readable as UTF-8 ({exc})")
    except OSError as exc:
        result.error(f"{path.name}: cannot read ({exc})")
    return None


def extract_title(text: str, article_name: str, result: Result) -> str | None:
    first_nonempty = next((line.strip() for line in text.splitlines() if line.strip()), "")
    match = H1_RE.fullmatch(first_nonempty)
    if not match:
        result.error(f"{article_name}: first non-empty line must be an H1 title")
        return None
    title = unicodedata.normalize("NFC", match.group(1).strip())
    if not title:
        result.error(f"{article_name}: title is empty")
        return None
    return title


def title_errors(
    title: str,
    label: str,
    max_chars: int | None,
    require_windows_safe: bool,
) -> list[str]:
    errors: list[str] = []
    if max_chars is not None and len(title) > max_chars:
        errors.append(f"{label}: title has {len(title)} code points; maximum is {max_chars}")
    if require_windows_safe:
        for char in title:
            code = ord(char)
            category = unicodedata.category(char)
            if char in INVALID_FILENAME_CHARS:
                errors.append(f"{label}: title contains Windows-invalid character {char!r}")
            elif category.startswith("C"):
                errors.append(
                    f"{label}: title contains a control, zero-width, or format character"
                )
            elif 0xFE00 <= code <= 0xFE0F or 0xE0100 <= code <= 0xE01EF:
                errors.append(f"{label}: title contains a variation selector")
        if title.rstrip() != title:
            errors.append(f"{label}: title has trailing whitespace")
        if title.endswith("."):
            errors.append(f"{label}: title cannot end with a dot")
    return sorted(set(errors))


def visible_body_count(text: str) -> int:
    """Count visible article characters under the skill's publication rule."""
    title_seen = False
    visible_parts: list[str] = []
    for line in text.splitlines():
        if not title_seen and H1_RE.fullmatch(line.strip()):
            title_seen = True
            continue
        if CAPTION_RE.match(line):
            continue
        line = IMAGE_RE.sub("", line)
        line = re.sub(r"<!--.*?-->", "", line)
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            continue
        stripped = re.sub(r"^#{1,6}\s*", "", stripped)
        stripped = re.sub(r"^>\s?", "", stripped)
        stripped = re.sub(r"^(?:[-+*]|\d+[.)])\s+", "", stripped)
        stripped = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", stripped)
        stripped = stripped.replace("**", "").replace("__", "").replace("`", "")
        visible_parts.append(stripped)
    return sum(1 for char in "".join(visible_parts) if not char.isspace())


def png_dimensions(data: bytes) -> tuple[int, int] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    return None


def gif_dimensions(data: bytes) -> tuple[int, int] | None:
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    return None


def bmp_dimensions(data: bytes) -> tuple[int, int] | None:
    if data.startswith(b"BM") and len(data) >= 26:
        width, height = struct.unpack("<ii", data[18:26])
        return width, abs(height)
    return None


def jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    pos = 2
    while pos < len(data):
        while pos < len(data) and data[pos] != 0xFF:
            pos += 1
        while pos < len(data) and data[pos] == 0xFF:
            pos += 1
        if pos >= len(data):
            break
        marker = data[pos]
        pos += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if pos + 2 > len(data):
            break
        length = int.from_bytes(data[pos : pos + 2], "big")
        if length < 2 or pos + length > len(data):
            break
        if marker in sof_markers and length >= 7:
            height = int.from_bytes(data[pos + 3 : pos + 5], "big")
            width = int.from_bytes(data[pos + 5 : pos + 7], "big")
            return width, height
        pos += length
    return None


def webp_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    pos = 12
    while pos + 8 <= len(data):
        chunk = data[pos : pos + 4]
        size = int.from_bytes(data[pos + 4 : pos + 8], "little")
        payload = data[pos + 8 : pos + 8 + size]
        if chunk == b"VP8X" and len(payload) >= 10:
            width = 1 + int.from_bytes(payload[4:7], "little")
            height = 1 + int.from_bytes(payload[7:10], "little")
            return width, height
        if chunk == b"VP8L" and len(payload) >= 5 and payload[0] == 0x2F:
            bits = int.from_bytes(payload[1:5], "little")
            width = 1 + (bits & 0x3FFF)
            height = 1 + ((bits >> 14) & 0x3FFF)
            return width, height
        if chunk == b"VP8 " and len(payload) >= 10 and payload[3:6] == b"\x9d\x01\x2a":
            width = int.from_bytes(payload[6:8], "little") & 0x3FFF
            height = int.from_bytes(payload[8:10], "little") & 0x3FFF
            return width, height
        pos += 8 + size + (size % 2)
    return None


def detect_dimensions(data: bytes) -> tuple[str, int, int] | None:
    for name, detector in (
        ("PNG", png_dimensions),
        ("JPEG", jpeg_dimensions),
        ("WEBP", webp_dimensions),
        ("GIF", gif_dimensions),
        ("BMP", bmp_dimensions),
    ):
        dimensions = detector(data)
        if dimensions:
            return name, dimensions[0], dimensions[1]
    return None


def expected_extension(format_name: str) -> set[str]:
    return {
        "JPEG": {".jpg", ".jpeg"},
        "PNG": {".png"},
        "WEBP": {".webp"},
        "GIF": {".gif"},
        "BMP": {".bmp"},
    }[format_name]


def parse_manifest(text: str, result: Result) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        header = MANIFEST_HEADER_RE.fullmatch(line)
        if header:
            current = {"序号": header.group(1)}
            entries.append(current)
            continue
        if current is None:
            result.error(f"插图网址.txt:{line_number}: content appears before [插图 NN]")
            continue
        if "：" in line:
            key, value = line.split("：", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            result.error(f"插图网址.txt:{line_number}: expected a key-value line")
            continue
        key = key.strip()
        value = value.strip()
        if key in current:
            result.error(f"插图网址.txt:{line_number}: duplicate field {key}")
        current[key] = value
    return entries


def validate_images(
    folder: Path,
    image_paths: list[Path],
    final_text: str | None,
    result: Result,
) -> None:
    if not image_paths:
        return
    numbers: list[int] = []
    for path in image_paths:
        match = IMAGE_NAME_RE.fullmatch(path.name)
        if match:
            numbers.append(int(match.group(1)))
    numbers.sort()
    if numbers != list(range(1, len(image_paths) + 1)):
        result.error(f"image sequence must be contiguous from 01; found {numbers}")

    hashes: dict[str, str] = {}
    measured: dict[str, tuple[int, int]] = {}
    for path in image_paths:
        try:
            data = path.read_bytes()
        except OSError as exc:
            result.error(f"{path.name}: cannot read image ({exc})")
            continue
        if not data:
            result.error(f"{path.name}: image is empty")
            continue
        detected = detect_dimensions(data)
        if not detected:
            result.error(f"{path.name}: signature is not a supported image")
            continue
        format_name, width, height = detected
        if path.suffix.lower() not in expected_extension(format_name):
            result.error(
                f"{path.name}: extension {path.suffix!r} does not match {format_name}"
            )
        if max(width, height) < 1200:
            result.warning(
                f"{path.name}: long edge is {max(width, height)}; manifest must document the exception"
            )
        digest = hashlib.sha256(data).hexdigest()
        if digest in hashes:
            result.error(f"{path.name}: duplicates image content from {hashes[digest]}")
        else:
            hashes[digest] = path.name
        measured[path.name] = (width, height)
        result.detail(f"image {path.name}: {format_name} {width}x{height}")

    manifest_path = folder / "插图网址.txt"
    if not manifest_path.exists():
        result.error("插图网址.txt is required when images are delivered")
        return
    manifest_text = read_utf8(manifest_path, result)
    if manifest_text is None:
        return
    entries = parse_manifest(manifest_text, result)
    if len(entries) != len(image_paths):
        result.error(
            f"manifest has {len(entries)} entries but folder has {len(image_paths)} images"
        )

    by_filename: dict[str, dict[str, str]] = {}
    for entry in entries:
        sequence = entry.get("序号", "??")
        missing = MANIFEST_FIELDS - entry.keys()
        extra = set(entry) - MANIFEST_FIELDS - {"序号", "分辨率说明"}
        if missing:
            result.error(f"manifest image {sequence}: missing fields {sorted(missing)}")
        if extra:
            result.error(f"manifest image {sequence}: unexpected fields {sorted(extra)}")
        filename = entry.get("本地文件名", "")
        if filename in by_filename:
            result.error(f"manifest image {sequence}: duplicate local filename {filename}")
        by_filename[filename] = entry
        if entry.get("确认状态") != "已下载并验证":
            result.error(f"manifest image {sequence}: 确认状态 must be 已下载并验证")
        if not entry.get("授权状态", "").startswith(("已确认可复用", "需人工确认")):
            result.error(
                f"manifest image {sequence}: 授权状态 must be 已确认可复用 or 需人工确认"
            )
        for field_name in ("直接图片 URL", "来源页面"):
            parsed = urlparse(entry.get(field_name, ""))
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                result.error(f"manifest image {sequence}: {field_name} must be an http(s) URL")
        if not all(entry.get(name, "").strip() for name in MANIFEST_FIELDS):
            continue
        dimensions_match = re.fullmatch(r"(\d+)\s*[×xX]\s*(\d+)", entry["图片尺寸"])
        if not dimensions_match:
            result.error(f"manifest image {sequence}: invalid 图片尺寸 format")
            continue
        recorded = (int(dimensions_match.group(1)), int(dimensions_match.group(2)))
        if filename in measured and recorded != measured[filename]:
            result.error(
                f"manifest image {sequence}: dimensions {recorded} do not match measured {measured[filename]}"
            )
        if filename in measured and max(measured[filename]) < 1200 and not entry.get(
            "分辨率说明"
        ):
            result.error(
                f"manifest image {sequence}: add 分辨率说明 for image below 1200-pixel long edge"
            )

    local_names = {path.name for path in image_paths}
    if set(by_filename) != local_names:
        result.error(
            "manifest filenames do not match local images; "
            f"missing entries={sorted(local_names - set(by_filename))}, "
            f"missing files={sorted(set(by_filename) - local_names)}"
        )

    if final_text is not None:
        embeds = [target for target in IMAGE_RE.findall(final_text)]
        embed_names = [Path(target).name if "://" not in target else target for target in embeds]
        counts = Counter(embed_names)
        if set(counts) != local_names:
            result.error(
                "final article embeds do not match local images; "
                f"missing embeds={sorted(local_names - set(counts))}, "
                f"missing files={sorted(set(counts) - local_names)}"
            )
        duplicates = sorted(name for name, count in counts.items() if count != 1)
        if duplicates:
            result.error(f"each image must be embedded exactly once; duplicated: {duplicates}")


def validate_knowledge_base(path: Path, require_ledger: bool, result: Result) -> None:
    text = read_utf8(path, result)
    if text is None:
        return
    if not SOURCE_ID_RE.search(text):
        result.error("知识库.md: no source IDs found")
    if not re.search(
        r"^##\s+(?:\d+\.\s*)?(?:Source index|来源索引)\s*$",
        text,
        re.MULTILINE,
    ):
        result.error("知识库.md: missing source index section")
    if not require_ledger:
        return
    ledger_match = re.search(
        r"^##\s+(?:\d+\.\s*)?终稿事实核对\s*$(.*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not ledger_match:
        result.error("知识库.md: missing 终稿事实核对 section")
    elif not re.search(r"^\|.*\[S\d{2,}\].*\|", ledger_match.group(1), re.MULTILINE):
        result.error("知识库.md: 终稿事实核对 has no source-linked rows")


def check_publishable_text(text: str, label: str, result: Result) -> None:
    if SOURCE_ID_RE.search(text):
        result.error(f"{label}: source IDs are forbidden in publishable prose")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if EDITOR_ARTIFACT_RE.match(line) or "[TODO:" in line:
            result.error(f"{label}:{line_number}: editorial artifact or placeholder remains")


def classify_status(folder: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    return "partial" if "_部分完成_" in folder.name else "complete"


def validate_folder(
    folder: Path,
    status: str,
    minimum: int | None,
    maximum: int | None,
    staging: bool,
) -> Result:
    result = Result(status=status, folder=folder)
    if not folder.is_dir():
        result.error(f"folder does not exist: {folder}")
        return result

    all_entries = list(folder.iterdir())
    subdirectories = [path.name for path in all_entries if path.is_dir()]
    if subdirectories:
        result.error(f"delivery folder must not contain subdirectories: {subdirectories}")
    files = [path for path in all_entries if path.is_file()]
    image_paths = [path for path in files if path.name.startswith("插图-")]

    if status == "complete" and "_部分完成_" in folder.name:
        result.error("complete delivery folder name must not contain _部分完成_")
    if status == "partial" and not staging and "_部分完成_" not in folder.name:
        result.error("partial delivery folder name must contain _部分完成_")
    if status == "partial" and not any(path.name == STATUS_FILE for path in files):
        result.error(f"partial delivery requires {STATUS_FILE}")

    for path in image_paths:
        if not IMAGE_NAME_RE.fullmatch(path.name):
            result.error(f"invalid image filename: {path.name}")

    compact_paths = [path for path in files if path.name.endswith(COMPACT_SUFFIX)]
    if len(compact_paths) > 1:
        result.error(f"multiple compact article files found: {[p.name for p in compact_paths]}")

    allowed_docs = set(BASE_DOCS)
    if status == "partial":
        allowed_docs.add(STATUS_FILE)
    allowed_names = allowed_docs | {path.name for path in image_paths} | {
        path.name for path in compact_paths
    }
    unexpected = [path.name for path in files if path.name not in allowed_names]
    if unexpected:
        result.error(f"unexpected files in delivery folder: {unexpected}")

    if status == "complete":
        missing = BASE_DOCS - {path.name for path in files}
        if missing:
            result.error(f"complete delivery is missing documents: {sorted(missing)}")
        if len(compact_paths) != 1:
            result.error("complete delivery requires exactly one compact article")
        if not 5 <= len(image_paths) <= 10:
            result.error(f"complete delivery requires 5-10 images; found {len(image_paths)}")
        if not (folder / "插图网址.txt").exists():
            result.error("complete delivery requires 插图网址.txt")
    elif status == "partial":
        useful_names = {path.name for path in files} - {STATUS_FILE}
        if not useful_names:
            result.error("partial delivery contains no useful output besides its status file")
        if image_paths and not (folder / "插图网址.txt").exists():
            result.error("partial delivery with images requires 插图网址.txt")
        if (folder / "插图网址.txt").exists() and not image_paths:
            result.error("插图网址.txt must not be delivered without local images")

    article_texts: dict[str, str] = {}
    for doc_name in ("初稿.md", "终稿.md"):
        path = folder / doc_name
        if not path.exists():
            continue
        text = read_utf8(path, result)
        if text is None:
            continue
        article_texts[doc_name] = text
        title = extract_title(text, doc_name, result)
        if title:
            for problem in title_errors(title, doc_name, None, False):
                result.error(problem)
            result.detail(f"{doc_name} title: {title!r}")
        count = visible_body_count(text)
        result.detail(f"{doc_name} visible body characters: {count}")
        if minimum is not None and count < minimum:
            result.error(f"{doc_name}: body has {count} characters; minimum is {minimum}")
        if maximum is not None and count > maximum:
            result.error(f"{doc_name}: body has {count} characters; maximum is {maximum}")
        check_publishable_text(text, doc_name, result)

    if compact_paths:
        compact_path = compact_paths[0]
        compact_text = read_utf8(compact_path, result)
        if compact_text is not None:
            compact_title = extract_title(compact_text, compact_path.name, result)
            if compact_title:
                for problem in title_errors(compact_title, compact_path.name, 20, True):
                    result.error(problem)
                expected_name = compact_title + COMPACT_SUFFIX
                if compact_path.name != expected_name:
                    result.error(
                        f"compact filename must equal title plus suffix; expected {expected_name!r}"
                    )
                result.detail(f"compact title: {compact_title!r} ({len(compact_title)} code points)")
            compact_count = visible_body_count(compact_text)
            result.detail(f"compact visible body characters: {compact_count}")
            if compact_count > 900:
                result.error(f"compact body has {compact_count} characters; maximum is 900")
            if IMAGE_RE.search(compact_text) or CAPTION_RE.search(compact_text):
                result.error("compact article must not contain images or image captions")
            check_publishable_text(compact_text, compact_path.name, result)

    if (folder / "知识库.md").exists():
        validate_knowledge_base(
            folder / "知识库.md",
            require_ledger=(
                "终稿.md" in article_texts or bool(compact_paths) or status == "complete"
            ),
            result=result,
        )

    final_text = article_texts.get("终稿.md")
    if image_paths or (folder / "插图网址.txt").exists():
        validate_images(folder, image_paths, final_text, result)

    if status == "partial":
        status_path = folder / STATUS_FILE
        if status_path.exists():
            status_text = read_utf8(status_path, result)
            if status_text is not None:
                for field_name in STATUS_FIELDS:
                    pattern = rf"^{re.escape(field_name)}[：:]\s*\S"
                    if not re.search(pattern, status_text, re.MULTILINE):
                        result.error(
                            f"{STATUS_FILE}: missing non-empty field {field_name}"
                        )
                if not re.search(
                    r"^状态[：:]\s*部分完成\s*$",
                    status_text,
                    re.MULTILINE,
                ):
                    result.error(f"{STATUS_FILE}: must contain 状态：部分完成")
                if not re.search(
                    r"^字数范围[：:]\s*[1-9]\d*\s*[-–—至]\s*[1-9]\d*",
                    status_text,
                    re.MULTILINE,
                ):
                    result.error(f"{STATUS_FILE}: 字数范围 must contain two positive bounds")
    return result


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--status", choices=("auto", "complete", "partial"), default="auto")
    parser.add_argument(
        "--staging",
        action="store_true",
        help="skip the final partial-folder name check during pre-package validation",
    )
    parser.add_argument("--min", type=int, dest="minimum")
    parser.add_argument("--max", type=int, dest="maximum")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.minimum is not None and args.minimum <= 0:
        print("ERROR: --min must be positive", file=sys.stderr)
        return 2
    if args.maximum is not None and args.maximum <= 0:
        print("ERROR: --max must be positive", file=sys.stderr)
        return 2
    if (
        args.minimum is not None
        and args.maximum is not None
        and args.minimum >= args.maximum
    ):
        print("ERROR: --min must be smaller than --max", file=sys.stderr)
        return 2

    folder = args.folder.resolve()
    status = classify_status(folder, args.status)
    result = validate_folder(folder, status, args.minimum, args.maximum, args.staging)
    for message in result.details:
        print(f"INFO: {message}")
    for message in result.warnings:
        print(f"WARNING: {message}")
    for message in result.errors:
        print(f"ERROR: {message}", file=sys.stderr)
    if result.errors:
        print(
            f"FAIL {status}: {folder} ({len(result.errors)} error(s))",
            file=sys.stderr,
        )
        return 1
    print(f"PASS {status}: {folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
