#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

from automation_common import (
    discussion_number_from,
    extract_pdf_url,
    fail,
    get_discussion,
    load_data,
    patch_discussion_links,
    parse_issue_body,
    save_pdf_attachment,
    save_data,
    set_output,
    update_discussion,
    validate_url,
)
from generate_thumbnail import main as generate_thumbnail
from generate_readme import main as generate_readme


def main() -> int:
    sections = parse_issue_body(os.environ.get("ISSUE_BODY", ""))
    discussion_number = discussion_number_from(sections.get("Discussion URL 또는 번호", ""))
    pdf_url = extract_pdf_url(sections.get("발표 자료 PDF", ""))
    youtube_url = validate_url(sections.get("유튜브 URL", ""), "유튜브 URL")
    if not pdf_url and not youtube_url:
        fail("발표 자료 PDF 또는 유튜브 URL 중 하나 이상을 입력해야 합니다")

    data = load_data()
    topic = next((item for item in data["topics"] if int(item["discussion_number"]) == discussion_number), None)
    if topic is None:
        fail(f"Discussion #{discussion_number}에 해당하는 자동화 데이터를 찾을 수 없습니다")

    if pdf_url:
        material_path, thumbnail_path = save_pdf_attachment(pdf_url, int(topic["round"]), topic["presenter"], topic["title"])
        topic["material_path"] = material_path
        topic["thumbnail_path"] = thumbnail_path
    if youtube_url:
        topic["youtube_url"] = youtube_url

    current_discussion = get_discussion(topic["discussion_id"])
    discussion_title = f"[{topic['round']}회차] {topic['title']}"
    discussion_body = patch_discussion_links(current_discussion["body"], topic)
    discussion = update_discussion(topic["discussion_id"], discussion_title, discussion_body)
    topic["discussion_url"] = discussion["url"]
    save_data(data)
    generate_thumbnail()
    generate_readme()

    set_output("round", str(topic["round"]))
    set_output("presenter", topic["presenter"])
    set_output("title", topic["title"])
    set_output("discussion_url", discussion["url"])
    print(f"updated discussion: {discussion['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
