from __future__ import annotations

import re
import hashlib
from datetime import datetime
from pydantic import BaseModel, Field


class SchoolNotice(BaseModel):
    title: str
    url: str
    text: str
    metadata: dict = Field(default_factory=dict)
    hash: str


def process_to_documents(raw_data: list[dict]) -> list[SchoolNotice]:
    docs = []
    for item in raw_data:
        content_hash = hashlib.sha256(item["text"].encode()).hexdigest()

        category_match = re.match(r"\[(.*?)\]", item["title"])
        category = category_match.group(1) if category_match else "일반"

        doc = SchoolNotice(
            title=item["title"],
            url=item["url"],
            text=item["text"],
            metadata={
                "category": category,
                "published_at": item["date"],
                "collected_at": datetime.now().isoformat(),
            },
            hash=content_hash,
        )
        docs.append(doc)
    return docs


# 에이전트에게 제공할 Tool Calling 스키마
ice_notice_tool = {
    "name": "search_ice_notices",
    "description": (
        "영남대학교 정보통신공학과 공지사항 DB에서 정보를 검색합니다. "
        "장학금, 졸업요건, 수강신청, 특강 등 학과 생활에 필요한 최신 공지를 찾을 때 사용합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "사용자가 궁금해하는 검색어 (예: '국가장학금 마감일', '졸업작품 제출')",
            },
            "category": {
                "type": "string",
                "description": "공지 카테고리 (장학, 학사, 일반 등)",
                "enum": ["장학", "학사", "일반", "취업"],
            },
        },
        "required": ["query"],
    },
}
