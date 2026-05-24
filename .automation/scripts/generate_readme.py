#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from automation_common import README_FILE, category_label, load_data, markdown_link_or_pending, material_link, presenter_link, thumbnail_link, topic_sort_key


START = "<!-- AUTO-GENERATED:TOPICS:START -->"
END = "<!-- AUTO-GENERATED:TOPICS:END -->"


def render_topics() -> str:
    topics = sorted(load_data().get("topics") or [], key=topic_sort_key)
    lines = [
        START,
        "| 발표 자료(클릭 시 확인 가능) | 발표 정보 |",
        "|---|---|",
    ]
    if not topics:
        lines.append("| 등록된 발표가 없습니다. | - |")
    for topic in topics:
        lines.append(f"| {render_material(topic)} | {render_info(topic)} |")
    lines.append(END)
    return "\n".join(lines)


def render_material(topic: dict) -> str:
    link = material_link(topic)
    if not link:
        return "업로드 예정"
    thumbnail = thumbnail_link(topic)
    if thumbnail:
        return f'<div align="center"><a href="{link}"><img src="{thumbnail}" width="100%"/></a></div>'
    return f"[발표 자료]({link})"


def render_info(topic: dict) -> str:
    items = [
        f"**회차:** {topic['round']}회차",
        f"**발표일:** {topic['date']}",
        f"**카테고리:** {category_label(topic['category'])}",
        f"**발표자:** {presenter_link(topic['presenter'])}",
        f"**발표 주제:** {escape_table_cell(topic['title'])}",
        f"**Discussion:** [바로가기]({topic['discussion_url']})",
        f"**발표 영상:** {markdown_link_or_pending(topic.get('youtube_url', ''), '발표 영상')}",
    ]
    return "<br>".join(items)


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
