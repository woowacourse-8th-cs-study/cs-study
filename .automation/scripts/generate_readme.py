#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from automation_common import README_FILE, load_data, markdown_link_or_pending, presenter_link, topic_sort_key


START = "<!-- AUTO-GENERATED:TOPICS:START -->"
END = "<!-- AUTO-GENERATED:TOPICS:END -->"


def render_topics() -> str:
    topics = sorted(load_data().get("topics") or [], key=topic_sort_key)
    lines = [
        START,
        "| 회차 | 발표일 | 카테고리 | 발표자 | 발표 주제 | 발표 자료 | 발표 영상 | Discussion |",
        "|---|---|---|---|---|---|---|---|",
    ]
    if not topics:
        lines.append("| - | - | - | - | 등록된 발표가 없습니다. | - | - | - |")
    for topic in topics:
        lines.append(
            "| {round}회차 | {date} | {category} | {presenter} | {title} | {material} | {youtube} | {discussion} |".format(
                round=topic["round"],
                date=topic["date"],
                category=topic["category"],
                presenter=presenter_link(topic["presenter"]),
                title=escape_table_cell(topic["title"]),
                material=markdown_link_or_pending(topic.get("material_url", ""), "발표 자료"),
                youtube=markdown_link_or_pending(topic.get("youtube_url", ""), "발표 영상"),
                discussion=f"[바로가기]({topic['discussion_url']})",
            )
        )
    lines.append(END)
    return "\n".join(lines)


def escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def replace_generated_block(readme: str, generated: str) -> str:
    if START not in readme or END not in readme:
        return readme.rstrip() + "\n\n## 📚 발표 자료 아카이브\n\n" + generated + "\n"
    before = readme.split(START, 1)[0].rstrip()
    after = readme.split(END, 1)[1].lstrip()
    return before + "\n\n" + generated + "\n\n" + after


def main() -> int:
    README_FILE.write_text(replace_generated_block(README_FILE.read_text(), render_topics()))
    print(f"wrote {README_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
