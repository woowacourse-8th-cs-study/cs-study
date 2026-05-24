from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT / ".automation" / "topics.yml"
README_FILE = ROOT / "README.md"

OWNER = "woowacourse-8th-cs-study"
REPO = "cs-study"

NO_RESPONSE_PLACEHOLDERS = {"", "_No response_"}

PRESENTERS = {
    "스타크": "MODUGGAGI",
    "로지": "Jihyun3478",
    "초록": "2Jaeheon",
    "러키": "Jiihyun",
    "도우너": "Soojin6943",
    "피즈": "wontop02",
}

CATEGORIES = [
    "Network",
    "Database",
    "Operating System",
    "Data Structure",
    "Algorithm",
    "Computer Architecture",
    "Spring",
    "Java",
    "Security",
    "Infra",
]


def parse_issue_body(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []
    for line in body.replace("\r\n", "\n").split("\n"):
        match = re.match(r"^###\s+(.+?)\s*$", line)
        if match:
            if current_key is not None:
                sections[current_key] = clean_value("\n".join(current_lines))
            current_key = match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_key is not None:
        sections[current_key] = clean_value("\n".join(current_lines))
    return sections


def clean_value(value: str) -> str:
    stripped = value.strip()
    return "" if stripped in NO_RESPONSE_PLACEHOLDERS else stripped


def fail(message: str) -> None:
    set_output("error", message)
    print(f"::error::{message}", file=sys.stderr)
    sys.exit(1)


def set_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a") as output:
        output.write(f"{name}<<__EOF__\n{value}\n__EOF__\n")


def load_data() -> dict:
    if not DATA_FILE.exists():
        return {"topics": []}
    data = yaml.safe_load(DATA_FILE.read_text()) or {}
    data.setdefault("topics", [])
    return data


def save_data(data: dict) -> None:
    DATA_FILE.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False, width=1000))


def validate_required(value: str, label: str) -> str:
    if not value:
        fail(f"{label} 값이 비어있습니다")
    return value


def validate_round(value: str) -> int:
    value = validate_required(value, "회차")
    match = re.search(r"\d+", value)
    if not match:
        fail(f"회차는 숫자를 포함해야 합니다: {value!r}")
    round_no = int(match.group(0))
    if round_no < 0 or round_no > 999:
        fail(f"회차 범위가 잘못되었습니다: {round_no}")
    return round_no


def validate_date(value: str) -> str:
    value = validate_required(value, "발표일")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        fail(f"발표일은 YYYY-MM-DD 형식이어야 합니다: {value!r}")
    return value


def validate_presenter(value: str) -> str:
    value = validate_required(value, "발표자")
    if value not in PRESENTERS:
        fail(f"지원하지 않는 발표자입니다: {value!r}")
    return value


def validate_category(value: str) -> str:
    value = validate_required(value, "카테고리")
    if value not in CATEGORIES:
        fail(f"지원하지 않는 카테고리입니다: {value!r}")
    return value


def validate_url(value: str, label: str) -> str:
    if not value:
        return ""
    if not re.match(r"^https?://", value):
        fail(f"{label}은 http:// 또는 https:// URL이어야 합니다: {value!r}")
    return value


def discussion_number_from(value: str) -> int:
    value = validate_required(value, "Discussion URL 또는 번호")
    if value.isdigit():
        return int(value)
    match = re.search(r"/discussions/(\d+)(?:\D|$)", value)
    if not match:
        fail(f"Discussion 번호를 찾을 수 없습니다: {value!r}")
    return int(match.group(1))


def presenter_link(name: str) -> str:
    login = PRESENTERS.get(name)
    return f"[{name}](https://github.com/{login})" if login else name


def markdown_link_or_pending(url: str, label: str) -> str:
    return f"[{label}]({url})" if url else "업로드 예정"


def topic_sort_key(topic: dict) -> tuple:
    return (int(topic["round"]), topic.get("date", ""), topic.get("presenter", ""), topic.get("title", ""))


def render_discussion_body(topic: dict) -> str:
    lines = [
        "## 🚀 발표 주제",
        topic["title"],
        "",
        "---",
        "",
        "## 📅 발표일",
        topic["date"],
        "",
        "## 🙋 발표자",
        topic["presenter"],
        "",
        "## 🗂️ 카테고리",
        topic["category"],
        "",
        "## 📚 발표 자료",
        markdown_link_or_pending(topic.get("material_url", ""), "발표 자료"),
        "",
        "## 🎥 발표 영상",
        markdown_link_or_pending(topic.get("youtube_url", ""), "발표 영상"),
        "",
        "---",
        "",
        "## 🎯 핵심 개념 요약",
        topic.get("summary") or "_작성 예정_",
        "",
        "## 🔗 미션과의 연결",
        topic.get("mission") or "_작성 예정_",
        "",
        "## 📚 참고 자료",
        topic.get("references") or "_작성 예정_",
        "",
        "---",
        "",
        "## 🙋‍♀️ 질문",
        "",
    ]
    return "\n".join(lines)


def graphql(query: str, variables: dict) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        fail("GITHUB_TOKEN 환경변수가 필요합니다")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        fail(f"GitHub GraphQL 요청 실패: HTTP {error.code}\n{detail}")
    except urllib.error.URLError as error:
        fail(f"GitHub GraphQL 요청 실패: {error}")
    if payload.get("errors"):
        fail(json.dumps(payload["errors"], ensure_ascii=False))
    return payload["data"]


def repository_info() -> tuple[str, dict[str, str]]:
    data = graphql(
        """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            id
            discussionCategories(first: 50) {
              nodes { id name }
            }
          }
        }
        """,
        {"owner": OWNER, "name": REPO},
    )
    repository = data["repository"]
    categories = {node["name"]: node["id"] for node in repository["discussionCategories"]["nodes"]}
    return repository["id"], categories


def create_discussion(repository_id: str, category_id: str, title: str, body: str) -> dict:
    data = graphql(
        """
        mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
          createDiscussion(input: {repositoryId: $repositoryId, categoryId: $categoryId, title: $title, body: $body}) {
            discussion { id number url }
          }
        }
        """,
        {"repositoryId": repository_id, "categoryId": category_id, "title": title, "body": body},
    )
    return data["createDiscussion"]["discussion"]


def update_discussion(discussion_id: str, title: str, body: str) -> dict:
    data = graphql(
        """
        mutation($discussionId: ID!, $title: String!, $body: String!) {
          updateDiscussion(input: {discussionId: $discussionId, title: $title, body: $body}) {
            discussion { id number url }
          }
        }
        """,
        {"discussionId": discussion_id, "title": title, "body": body},
    )
    return data["updateDiscussion"]["discussion"]
