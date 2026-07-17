import json

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from enum import Enum


class GradeEnum(str, Enum):
    GRADE_10 = "高一"
    GRADE_11 = "高二"
    GRADE_12 = "高三"


class TaskStatusEnum(str, Enum):
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    EXPIRED = "已过期"


class StudentRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="学生姓名")
    email: EmailStr = Field(..., description="邮箱地址")
    grade: GradeEnum = Field(..., description="年级")
    password: str = Field(..., min_length=8, max_length=128, description="登录密码")


class StudentLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=128, description="登录密码")


class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    grade: str
    chat_mode: str = "explore_first"
    unlock_after_turns: int = 3
    onboarding_completed: bool = False
    registered_at: datetime
    operation_log: datetime

    class Config:
        from_attributes = True


class OnboardingCompleteRequest(BaseModel):
    interest_tags: List[str] = Field(default_factory=list, max_length=10)
    confusion_tags: List[str] = Field(default_factory=list, max_length=10)
    learning_style: Optional[str] = Field(None, max_length=50)


class TaskCreateRequest(BaseModel):
    student_email: EmailStr = Field(..., description="学生邮箱")
    description: str = Field(..., min_length=1, description="任务描述")
    deadline: Optional[datetime] = None


class TaskCompleteRequest(BaseModel):
    task_id: int = Field(..., description="任务ID")
    feedback: Optional[str] = Field(None, description="打卡反馈")


class TaskResponse(BaseModel):
    id: int
    student_id: int
    description: str
    status: TaskStatusEnum
    deadline: Optional[datetime] = None
    feedback: Optional[str] = None
    estimated_minutes: int
    growth_points: int
    topic_tags: List[str]
    created_at: datetime
    completed_at: Optional[datetime] = None
    operation_log: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("topic_tags", mode="before")
    @classmethod
    def parse_topic_tags(cls, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except (TypeError, json.JSONDecodeError):
                return []
        return value or []


class StudentWithTasksResponse(StudentResponse):
    tasks: List[TaskResponse] = []


class ApiResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(
        ...,
        description="消息角色：user/assistant",
    )
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="对话历史")
    student_name: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool = True
    reply: str = Field(..., description="AI 回复内容")
    mode: str = Field(..., description="对话模式：deerflow/mock")
    can_extract_task: bool = False


class ProfileUpdateRequest(BaseModel):
    interest_tags: Optional[List[str]] = None
    ability_tags: Optional[List[str]] = None
    exploration_stage: Optional[str] = Field(None, min_length=1, max_length=50)
    summary: Optional[str] = Field(None, max_length=1000)


class ProfileResponse(BaseModel):
    interest_tags: List[str] = Field(default_factory=list)
    ability_tags: List[str] = Field(default_factory=list)
    exploration_stage: str = "探索中"
    summary: str = ""
    welcome_message: str = ""
    updated_at: Optional[datetime] = None
    is_empty: bool = True
    guidance: Optional[str] = None


class ConversationMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationHistoryResponse(BaseModel):
    messages: List[ConversationMessageResponse] = Field(default_factory=list)


class TodayTasksResponse(BaseModel):
    primary_task: Optional[TaskResponse] = None
    tasks: List[TaskResponse] = Field(default_factory=list)


class GrowthResourceResponse(BaseModel):
    id: str
    title: str
    resource_type: str
    description: str
    url: Optional[str] = None
    reason: str


class GrowthResourceListResponse(BaseModel):
    personalized: bool
    resources: List[GrowthResourceResponse] = Field(default_factory=list)


class GrowthEventResponse(BaseModel):
    id: int
    task_id: Optional[int] = None
    event_type: str
    title: str
    description: Optional[str] = None
    growth_points: int
    topic_tags: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("topic_tags", mode="before")
    @classmethod
    def parse_topic_tags(cls, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except (TypeError, json.JSONDecodeError):
                return []
        return value or []


class GrowthEventListResponse(BaseModel):
    events: List[GrowthEventResponse] = Field(default_factory=list)


class GrowthSummaryResponse(BaseModel):
    days: int
    created_count: int
    completed_count: int
    growth_points: int
    top_interest: Optional[str] = None


class ExtractTaskRequest(BaseModel):
    student_email: EmailStr = Field(..., description="学生邮箱")
    messages: List[ChatMessage] = Field(..., description="对话历史")


class DeerFlowStatusResponse(BaseModel):
    online: bool = Field(False, description="DeerFlow gateway 是否在线")
    assistant_id: str = Field(..., description="当前 DeerFlow assistant ID")
    model: Optional[str] = Field(None, description="当前或默认模型名")
    error: Optional[str] = Field(None, description="离线或代理失败原因")
    raw: Optional[Dict[str, Any]] = Field(None, description="DeerFlow 原始返回")

    model_config = ConfigDict(extra="allow")


class SkillItem(BaseModel):
    name: str = Field(..., description="Skill 名称")
    description: Optional[str] = Field(None, description="Skill 描述")
    enabled: Optional[bool] = Field(None, description="Skill 是否启用，未知时为空")
    raw: Optional[Dict[str, Any]] = Field(None, description="DeerFlow 原始 skill 项")

    model_config = ConfigDict(extra="allow")


class SkillListResponse(BaseModel):
    online: bool = Field(False, description="DeerFlow gateway 是否在线")
    skills: List[SkillItem] = Field(default_factory=list, description="Skill 列表")
    error: Optional[str] = Field(None, description="离线或代理失败原因")
    raw: Optional[Dict[str, Any]] = Field(None, description="DeerFlow 原始返回")

    model_config = ConfigDict(extra="allow")


class SkillToggleRequest(BaseModel):
    enabled: bool = Field(..., description="是否启用该 skill")


class SkillToggleResponse(BaseModel):
    online: bool = Field(False, description="DeerFlow gateway 是否在线")
    skill: SkillItem = Field(..., description="切换后的 skill 状态；离线时仅保证 name 可用")
    error: Optional[str] = Field(None, description="离线或代理失败原因")
    raw: Optional[Dict[str, Any]] = Field(None, description="DeerFlow 原始返回")

    model_config = ConfigDict(extra="allow")


class ModelItem(BaseModel):
    id: str = Field(..., description="模型 ID")
    name: Optional[str] = Field(None, description="模型展示名")
    provider: Optional[str] = Field(None, description="模型提供方")
    raw: Optional[Dict[str, Any]] = Field(None, description="DeerFlow 原始 model 项")

    model_config = ConfigDict(extra="allow")


class ModelListResponse(BaseModel):
    online: bool = Field(False, description="DeerFlow gateway 是否在线")
    models: List[ModelItem] = Field(default_factory=list, description="模型列表")
    error: Optional[str] = Field(None, description="离线或代理失败原因")
    raw: Optional[Dict[str, Any]] = Field(None, description="DeerFlow 原始返回")

    model_config = ConfigDict(extra="allow")


class ChatModeSchema(str, Enum):
    EXPLORE_FIRST = "explore_first"
    BALANCED = "balanced"
    DIRECT_ACTION = "direct_action"


class PreferencesUpdateRequest(BaseModel):
    chat_mode: Optional[ChatModeSchema] = None
    unlock_after_turns: Optional[int] = Field(None, ge=2, le=8, description="解锁微行动所需的对话轮次，2-8 之间")


class PreferencesResponse(BaseModel):
    chat_mode: str
    unlock_after_turns: int
    chat_mode_label: str
    unlock_label: str


class StreamChatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    message: str = Field(..., min_length=1, description="用户发送的消息")
    conversation_id: Optional[int] = Field(None, description="会话 ID，为空时创建新会话")
    model_name: Optional[str] = Field(None, description="模型名称覆盖")
    thinking_enabled: bool = Field(False, description="是否启用思考模式")
    is_plan_mode: bool = Field(False, description="是否启用计划模式")
    file_ids: Optional[List[str]] = Field(None, description="上传的文件 ID 列表")


class ConversationCreateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    title: Optional[str] = Field(None, max_length=200, description="会话标题")
    model_name: Optional[str] = None
    thinking_enabled: bool = False
    is_plan_mode: bool = False


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    thread_id: str
    title: str
    model_name: Optional[str] = None
    thinking_enabled: bool = False
    is_plan_mode: bool = False
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: List[Dict[str, Any]] = Field(default_factory=list)


class ConversationUpdateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    title: Optional[str] = Field(None, max_length=200)
    model_name: Optional[str] = None
    thinking_enabled: Optional[bool] = None
    is_plan_mode: Optional[bool] = None


class ChatSuggestionsResponse(BaseModel):
    suggestions: List[str] = Field(default_factory=list)


class UploadFileResponse(BaseModel):
    filename: str
    file_id: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    error: Optional[str] = None


class UploadFilesResponse(BaseModel):
    files: List[UploadFileResponse] = Field(default_factory=list)
