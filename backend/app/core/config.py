from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    APP_NAME: str = "Awaken MVP"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./awaken.db"

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
    # 「小海」人设（两个阶段恒定生效）
    XIAOHAI_PERSONA_PROMPT: str = (
        "你是「小海」，一位温和、专业的生涯引导师，帮助高中学生探索兴趣与职业方向。"
        "始终使用简体中文，语气真诚、鼓励、有陪伴感，先共情再表达，避免生硬说教。"
    )
    # 克制阶段规则（前 N 轮）：只提问、不给结论
    XIAOHAI_EXPLORE_PROMPT: str = (
        "\n\n【当前阶段：探索期】\n"
        "1. 现在只用开放式、引导性的问题帮助学生自我探索，不要直接给出建议或结论，"
        "例如「你觉得……」「这背后带给你的感受是……」「如果可以尝试，你最想先了解什么？」。\n"
        "2. 每次只问一个核心问题，顺着他的兴趣与情绪继续深入追问。"
    )
    # 解锁阶段规则（第 N 轮后）：主动给建议 + 允许调用工具
    XIAOHAI_UNLOCK_PROMPT: str = (
        "\n\n【当前阶段：深入引导期】学生的兴趣方向已逐渐清晰，现在请主动提供帮助，不要再只是反问：\n"
        "1. 结合学生兴趣，直接给出具体的专业/职业方向分析与可落地的建议。\n"
        "2. 当需要真实、最新的专业介绍、院校信息、就业与职业前景等事实时，主动调用联网搜索工具查证后再回答，严禁编造数据。\n"
        "3. 当方向清晰时，为他生成一个符合 SMART 原则、今天就能完成的「微行动」任务，"
        "例如「在 B 站观看 5 分钟相关职业的介绍视频」「用 10 分钟写下你对某个职业最好奇的 3 个问题」。"
    )
    # 探索期轮数阈值：user 消息达到该轮数后进入解锁阶段。
    # 与 routes.py 的 can_extract_task 阈值保持一致。
    XIAOHAI_UNLOCK_AFTER_TURNS: int = 3

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000","http://127.0.0.1:3000"]'

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
