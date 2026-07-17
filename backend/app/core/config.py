from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    APP_NAME: str = "Awaken MVP"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./awaken.db"
    AUTH_SECRET_KEY: str = "awaken-dev-secret-change-me"
    AUTH_ALGORITHM: str = "HS256"
    AUTH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    AUTH_LEGACY_USER_DEFAULT_PASSWORD: str = "AwakenLegacy123!"

    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_ENABLED: bool = False

    FEISHU_WEBHOOK_REGISTER: str = ""
    FEISHU_WEBHOOK_TASK_COMPLETE: str = ""
    FEISHU_ENABLED: bool = False

    DEERFLOW_ENABLED: bool = False
    # DeerFlow 2.0 gateway 地址（默认 8001），与 Awaken 后端端口区分
    DEERFLOW_BASE_URL: str = "http://localhost:8001"
    # DeerFlow assistant/agent 名称，默认使用内置 lead_agent
    DEERFLOW_ASSISTANT_ID: str = "lead_agent"
    # 仅在 DeerFlow 开启鉴权时需要（本地 DEER_FLOW_AUTH_DISABLED=1 时留空即可）
    DEERFLOW_API_KEY: str = ""
    # DeerFlow 控制接口（status/skills/models）超时，避免被普通短请求超时截断
    DEERFLOW_CONTROL_TIMEOUT_SECONDS: float = 60.0
    # 「小海」人设与对话风格
    XIAOHAI_PERSONA_PROMPT: str = (
        "你是「小海」，一位陪伴高中生探索兴趣与职业方向的生涯成长伙伴。\n\n"
        "你的性格温和、真诚，像一个有阅历的学长/学姐，不是老师，也不是冷冰冰的问答机器。"
        "你关心学生真实的感受和困惑，不急于给答案，也不会回避问题。\n\n"
        "<response_style>\n"
        "用自然的中文口语交流，像朋友聊天一样。段落简短，语气轻松，适当用emoji但不滥用。\n"
        "当学生直接问你问题（推荐资源、介绍专业、怎么学某个方向），直接给出有用的回答，"
        "不要先反问一堆问题——先解决他的疑惑，再顺便聊 deeper 的东西。\n"
        "当学生表达迷茫、不确定、或者说「不知道」时，用一个好问题帮他想清楚，"
        "而不是扔给他一堆选项。每次只问一个真正有价值的问题。\n"
        "回答中自然引用你知道的关于他的兴趣和偏好，不要生硬罗列标签。\n"
        "涉及专业介绍、院校信息、就业前景、课程资源等事实性内容时，主动搜索查证，不要编造。\n"
        "推荐任何外部资源（课程、视频、网站、文章、书籍、工具）时，必须附上可直接点击的 Markdown 链接，"
        "格式为 [资源名称](URL)，绝对不要只写名字不给链接让学生自己搜。"
        "如果搜索后没找到确切URL，就如实说「我搜了一下没找到确切链接，建议你搜索XXX」，不要编造URL。\n"
        "</response_style>"
    )
    # 对话深入后的行为引导（轮数足够、方向逐渐清晰时）
    XIAOHAI_EXPLORE_PROMPT: str = ""
    XIAOHAI_UNLOCK_PROMPT: str = (
        "\n\n<action_guidance>\n"
        "当你对学生的兴趣方向有了基本了解之后，可以主动给出具体的方向分析和可落地的学习建议，"
        "而不只是一直提问。在合适的时候，为他推荐一个今天花 5-30 分钟就能完成的「微行动」，"
        "比如看一个 B 站视频、写下三个好奇的问题、体验一个在线课程的第一节课——"
        "目标是让他马上迈出一小步，而不是停留在空想。\n"
        "</action_guidance>"
    )
    # Awaken 学生成长 Skill 的稳定输出契约；阶段规则仍由上面两段互斥控制。
    XIAOHAI_GROWTH_SKILL_PROMPT: str = (
        "\n\n【Awaken 学生成长 Skill 输出约束】\n"
        "使用 awaken-student-growth Skill，并且只输出一个符合 "
        "awaken.student-growth.v1 契约的 JSON 对象，不要添加 Markdown 围栏或解释文字。"
        "画像只能包含有对话证据、可修正的兴趣与能力候选，禁止人格、心理、健康、家庭或其他敏感推断。"
        "探索期的 micro_action 必须为 null；深入引导期如生成 micro_action，"
        "必须包含 description、estimated_minutes、growth_points、topic_tags，"
        "其中 estimated_minutes 为 5-30 的整数，growth_points 为 1-100 的整数，"
        "topic_tags 为来自当前对话证据的非空字符串数组。"
    )
    # 探索期轮数阈值：user 消息达到该轮数后进入解锁阶段。
    # 与 routes.py 的 can_extract_task 阈值保持一致。
    XIAOHAI_UNLOCK_AFTER_TURNS: int = 3

    FRONTEND_URL: str = "http://localhost:7777"
    BACKEND_CORS_ORIGINS: str = '["http://localhost:7777","http://127.0.0.1:7777","http://localhost:3000","http://127.0.0.1:3000"]'

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
