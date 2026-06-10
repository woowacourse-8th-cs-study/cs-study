#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from automation_common import ROOT, fail, load_data, save_data


def needs_rebuild(thumbnail: Path, pdf: Path) -> bool:
    if not thumbnail.exists():
        return True
    return thumbnail.stat().st_mtime < pdf.stat().st_mtime


def extract_first_page(pdf: Path, thumbnail: Path) -> None:
    thumbnail.parent.mkdir(parents=True, exist_ok=True)
    prefix = thumbnail.with_suffix("")
    command = ["pdftoppm", "-png", "-r", "150", "-singlefile", "-f", "1", "-l", "1", str(pdf), str(prefix)]
    try:
        subprocess.run(command, check=True, capture_output=True)
    except FileNotFoundError:
        fail("pdftoppm을 찾을 수 없습니다. poppler-utils 설치가 필요합니다.")
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.decode(errors="replace")
        fail(f"썸네일 추출 실패: {pdf}\n{stderr}")
    if not thumbnail.exists():
        fail(f"썸네일 파일이 생성되지 않았습니다: {thumbnail}")


def generate_topic_thumbnail(topic: dict) -> bool:
    material_path = topic.get("material_path")
    thumbnail_path = topic.get("thumbnail_path")
    if not material_path or not thumbnail_path:
        return False
    pdf = ROOT / material_path
    thumbnail = ROOT / thumbnail_path
    if not pdf.exists():
        fail(f"PDF 파일을 찾을 수 없습니다: {material_path}")
    if not needs_rebuild(thumbnail, pdf):
        return False
    extract_first_page(pdf, thumbnail)
    return True


def main() -> int:
    data = load_data()
    generated = 0
    skipped = 0
    for topic in data.get("topics") or []:
        if not topic.get("material_path") or not topic.get("thumbnail_path"):
            continue
        if generate_topic_thumbnail(topic):
            generated += 1
        else:
            skipped += 1
    save_data(data)
    print(f"done. generated={generated} skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
