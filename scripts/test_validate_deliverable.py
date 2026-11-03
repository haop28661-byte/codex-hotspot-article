#!/usr/bin/env python3
"""Focused tests for validate_deliverable.py."""

from __future__ import annotations

import binascii
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

import validate_deliverable as validator


def png_bytes(width: int, height: int, marker: int) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        content = kind + payload
        return (
            struct.pack(">I", len(payload))
            + content
            + struct.pack(">I", binascii.crc32(content) & 0xFFFFFFFF)
        )

    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            row.extend((marker + x + y) % 256 for _ in range(3))
        rows.append(bytes(row))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + chunk(b"IEND", b"")
    )


def write_complete_fixture(folder: Path) -> None:
    folder.mkdir()
    title = "短标题一二三四五六七八"
    long_title = "长稿标题：可以更完整地说明这件事"
    (folder / "知识库.md").write_text(
        "# 知识库\n\n## Source index\n\n- [S01] source\n\n"
        "## 终稿事实核对\n\n| 文章 | 位置或短引文 | 主张类型 | 来源 ID | 支撑内容 | 核查结果 |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| 终稿 | 示例句 | 事实 | [S01] | source text | 已核对 |\n",
        encoding="utf-8",
    )
    (folder / "初稿.md").write_text(
        f"# {long_title}\n\n初稿正文。\n",
        encoding="utf-8",
    )

    image_blocks: list[str] = []
    manifest_blocks: list[str] = []
    for number in range(1, 6):
        filename = f"插图-{number:02d}-示例{number}.png"
        (folder / filename).write_bytes(png_bytes(1200, 4, number))
        image_blocks.append(
            f"![示例图注]({filename})\n\n*图注：示例图注*"
        )
        manifest_blocks.append(
            "\n".join(
                [
                    f"[插图 {number:02d}]",
                    f"本地文件名：{filename}",
                    "插入位置：在“正文之后”、“结尾之前”（示例小节）",
                    "建议图注：示例图注",
                    "图片尺寸：1200×4",
                    "直接图片 URL：https://example.com/image.png",
                    "来源页面：https://example.com/source",
                    "作者或机构：示例机构",
                    "授权与署名：CC BY 4.0，署名示例机构",
                    "授权状态：已确认可复用",
                    "确认状态：已下载并验证",
                ]
            )
        )
    final_text = (
        f"# {long_title}\n\n正文开始。\n\n"
        + "\n\n中间段落。\n\n".join(image_blocks)
        + "\n\n正文结束。\n"
    )
    (folder / "终稿.md").write_text(final_text, encoding="utf-8")
    (folder / "插图网址.txt").write_text(
        "\n\n".join(manifest_blocks) + "\n",
        encoding="utf-8",
    )
    (folder / f"{title}{validator.COMPACT_SUFFIX}").write_text(
        f"# {title}\n\n短版正文。\n",
        encoding="utf-8",
    )


def write_status_file(folder: Path, incomplete: str = "配图") -> None:
    (folder / validator.STATUS_FILE).write_text(
        "\n".join(
            [
                "主题：示例主题",
                "字数范围：600-1200字",
                "状态：部分完成",
                "已完成：研究与正文",
                f"未完成：{incomplete}",
                "临时工作区：C:\\Temp\\example",
                "下一步：补齐图片",
                "版权待确认：无",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class ValidatorTests(unittest.TestCase):
    def test_complete_fixture_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "示例主题"
            write_complete_fixture(folder)
            result = validator.validate_folder(folder, "complete", 1, 9999, False)
            self.assertEqual(result.errors, [])

    def test_extra_file_fails_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "示例主题"
            write_complete_fixture(folder)
            (folder / "notes.txt").write_text("extra", encoding="utf-8")
            result = validator.validate_folder(folder, "complete", 1, 9999, False)
            self.assertTrue(any("unexpected files" in error for error in result.errors))

    def test_long_compact_title_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "示例主题"
            write_complete_fixture(folder)
            old = next(folder.glob(f"*{validator.COMPACT_SUFFIX}"))
            old.unlink()
            title = "一二三四五六七八九十一二三四五六七八九十一"
            (folder / f"{title}{validator.COMPACT_SUFFIX}").write_text(
                f"# {title}\n\n短版正文。\n",
                encoding="utf-8",
            )
            result = validator.validate_folder(folder, "complete", 1, 9999, False)
            self.assertTrue(any("maximum is 20" in error for error in result.errors))

    def test_research_only_partial_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "示例主题_部分完成_20260101-1200"
            folder.mkdir()
            (folder / "知识库.md").write_text(
                "# 知识库\n\n## Source index\n\n- [S01] source\n",
                encoding="utf-8",
            )
            write_status_file(folder, incomplete="正文")
            result = validator.validate_folder(folder, "partial", None, None, False)
            self.assertEqual(result.errors, [])

    def test_text_complete_but_images_missing_is_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            staging = Path(temp) / "staging"
            write_complete_fixture(staging)
            for path in staging.glob("插图-*.png"):
                path.unlink()
            (staging / "插图网址.txt").unlink()
            write_status_file(staging)
            staged_result = validator.validate_folder(staging, "partial", 1, 9999, True)
            self.assertEqual(staged_result.errors, [])
            delivered = staging.rename(
                staging.parent / "示例主题_部分完成_20260101-1200"
            )
            delivered_result = validator.validate_folder(
                delivered, "partial", 1, 9999, False
            )
            self.assertEqual(delivered_result.errors, [])


if __name__ == "__main__":
    unittest.main()
