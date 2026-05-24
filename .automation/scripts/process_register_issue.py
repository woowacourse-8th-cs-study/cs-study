#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

from automation_common import (
    create_discussion,
    extract_pdf_url,
    fail,
    load_data,
    parse_issue_body,
    render_discussion_body,
    repository_info,
    save_pdf_attachment,
    save_data,
    set_output,
    validate_category,
    validate_date,
    validate_presenter,
    validate_required,
    validate_round,
    validate_url,
)
from generate_thumbnail import main as generate_thumbnail
from generate_readme import main as generate_readme


def main() -> int:
    sections = parse_issue_body(os.environ.get("ISSUE_BODY", ""))
    round_no = validate_round(sections.get("회차", ""))
    date = validate_date(sections.get("발표일", ""))
    presenter = validate_presenter(sections.get("발표자", ""))
    category = validate_category(sections.get("카테고리", ""))
    title = validate_required(sections.get("발표 주제", ""), "발표 주제")
    pdf_url = extract_pdf_url(sections.get("발표 자료 PDF", ""))
    youtube_url = validate_url(sections.get("유튜브 URL", ""), "유튜브 URL")

    data = load_data()
    for topic in data["topics"]:
        if int(topic["round"]) == round_no and topic["presenter"] == presenter:
            fail(f"{round_no}회차에 {presenter} 발표가 이미 등록되어 있습니다")

    repository_id, categories = repository_info()
    category_id = categories.get(category)
    if not category_id:
        fail(f"Discussion 카테고리 {category!r}가 없습니다. 레포 Settings > Discussions에서 먼저 생성해주세요.")

    topic = {
        "round": round_no,
        "date": date,
        "presenter": presenter,
        "category": category,
        "title": title,
        "youtube_url": youtube_url,
        "summary": sections.get("핵심 개념 요약", ""),
        "mission": sections.get("미션과의 연결", ""),
        "references": sections.get("참고 자료", ""),
    }
    material_path, thumbnail_path = save_pdf_attachment(pdf_url, round_no, presenter, title)
    if material_path:
        topic["material_path"] = material_path
        topic["thumbnail_path"] = thumbnail_path
    discussion_title = f"[{round_no}회차] {title}"
    discussion = create_discussion(repository_id, category_id, discussion_title, render_discussion_body(topic))
    topic.update(
        {
            "discussion_id": discussion["id"],
            "discussion_number": discussion["number"],
            "discussion_url": discussion["url"],
        }
    )
    data["topics"].append(topic)
    save_data(data)
    generate_thumbnail()
    generate_readme()

    set_output("round", str(round_no))
    set_output("presenter", presenter)
    set_output("title", title)
    set_output("discussion_url", discussion["url"])
    print(f"created discussion: {discussion['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
