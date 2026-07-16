import json
from collections import Counter
from typing import Dict, Iterable, List, Optional


PROFILE_GUIDANCE = "和小海聊聊你的兴趣与经历，逐步形成成长画像。"
GENERIC_RESOURCE_REASON = "适合当前年级与探索阶段的通用资源"

RESOURCE_CATALOG = (
    {
        "id": "robot-observation",
        "title": "校园机器人观察与拆解",
        "resource_type": "实践",
        "description": "观察校园中的自动化设备，并画出传感器、控制器和执行器的关系。",
        "url": None,
        "topic_tags": ("机器人", "物理"),
        "ability_tags": ("动手实践", "观察分析"),
        "grades": ("高一", "高二", "高三"),
        "stages": ("探索中", "聚焦中"),
    },
    {
        "id": "career-interview",
        "title": "一次真实职业访谈",
        "resource_type": "活动",
        "description": "选择一位熟悉的从业者，用五个问题了解真实工作内容。",
        "url": None,
        "topic_tags": ("职业探索",),
        "ability_tags": ("沟通表达",),
        "grades": ("高一", "高二", "高三"),
        "stages": ("探索中", "聚焦中"),
    },
    {
        "id": "project-planning",
        "title": "十五分钟项目计划课",
        "resource_type": "课程",
        "description": "学习把一个兴趣拆成可在今天启动的最小项目。",
        "url": None,
        "topic_tags": ("项目实践",),
        "ability_tags": ("规划执行",),
        "grades": ("高一", "高二", "高三"),
        "stages": ("探索中", "聚焦中"),
    },
    {
        "id": "science-question-challenge",
        "title": "校园科学问题挑战",
        "resource_type": "竞赛",
        "description": "从生活现象中提出一个可验证的问题，并设计小型实验。",
        "url": None,
        "topic_tags": ("物理", "科学"),
        "ability_tags": ("观察分析", "动手实践"),
        "grades": ("高一", "高二"),
        "stages": ("探索中", "聚焦中"),
    },
)


def parse_tags(value: Optional[str]) -> List[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def normalize_tags(values: Iterable[str]) -> List[str]:
    result = []
    seen = set()
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def encode_tags(values: Iterable[str]) -> str:
    return json.dumps(normalize_tags(values), ensure_ascii=False)


def recommend_resources(
    *,
    grade: str,
    interest_tags: Iterable[str],
    ability_tags: Iterable[str],
    exploration_stage: str,
    resource_type: Optional[str] = None,
) -> Dict[str, object]:
    interests = set(interest_tags)
    abilities = set(ability_tags)
    personalized = bool(interests or abilities)
    ranked = []

    for position, resource in enumerate(RESOURCE_CATALOG):
        if resource_type and resource["resource_type"] != resource_type:
            continue

        matched_interests = interests.intersection(resource["topic_tags"])
        matched_abilities = abilities.intersection(resource["ability_tags"])
        score = (
            len(matched_interests) * 4
            + len(matched_abilities) * 2
            + int(grade in resource["grades"])
            + int(exploration_stage in resource["stages"])
        )
        if personalized and matched_interests:
            reason = f"与你关注的{'、'.join(sorted(matched_interests))}方向相关"
        elif personalized and matched_abilities:
            reason = f"适合练习{'、'.join(sorted(matched_abilities))}"
        elif personalized:
            reason = "适合当前年级与探索阶段，可用于拓展新的方向"
        else:
            reason = GENERIC_RESOURCE_REASON

        ranked.append((
            -score,
            position,
            {
                "id": resource["id"],
                "title": resource["title"],
                "resource_type": resource["resource_type"],
                "description": resource["description"],
                "url": resource["url"],
                "reason": reason,
            },
        ))

    ranked.sort(key=lambda item: (item[0], item[1]))
    return {
        "personalized": personalized,
        "resources": [item[2] for item in ranked],
    }


def top_topic(tag_values: Iterable[str]) -> Optional[str]:
    counts = Counter()
    for value in tag_values:
        counts.update(parse_tags(value))
    if not counts:
        return None
    return sorted(counts, key=lambda tag: (-counts[tag], tag))[0]
