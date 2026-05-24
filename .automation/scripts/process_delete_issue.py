#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

from automation_common import (
    ROOT,
    delete_discussion,
    discussion_number_from,
    fail,
    load_data,
    parse_issue_body,
    save_data,
    set_output,
)
from generate_readme import main as generate_readme


def delete_local_file(path_text: str) -> str:
    if not path_text or path_text.startswith("http"):
        return ""
    path = ROOT / path_text
    if path.exists():
        path.unlink()
    return path_text


def main() -> int:
    sections = parse_issue_body(os.environ.get("ISSUE_BODY", ""))
    discussion_number = discussion_number_from(sections.get("Discussion 번호", ""))

    data = load_data()
    topics = data.get("topics") or []
    match = next(
        ((index, topic) for index, topic in enumerate(topics) if int(topic["discussion_number"]) == discussion_number),
        None,
    )
    if match is None:
        fail(f"Discussion #{discussion_number}에 해당하는 자동화 데이터를 찾을 수 없습니다")

    index, topic = match
    material_path = delete_local_file(topic.get("material_path", ""))
    thumbnail_path = delete_local_file(topic.get("thumbnail_path", ""))
    delete_discussion(topic["discussion_id"])
    topics.pop(index)
    save_data(data)
    generate_readme()

    set_output("round", str(topic["round"]))
    set_output("presenter", topic["presenter"])
    set_output("title", topic["title"])
    set_output("discussion_number", str(discussion_number))
    set_output("material_path", material_path)
    set_output("thumbnail_path", thumbnail_path)
    print(f"deleted discussion #{discussion_number}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
