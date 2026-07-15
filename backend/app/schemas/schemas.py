from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from typing import Any, Dict, Optional, List
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
    registered_at: datetime
    operation_log: datetime

    class Config:
        from_attributes = True


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
    created_at: datetime
    completed_at: Optional[datetime] = None
    operation_log: datetime

    class Config:
        from_attributes = True


class StudentWithTasksResponse(StudentResponse):
    tasks: List[TaskResponse] = []


class ApiResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None


class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色：user/assistant/system")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="对话历史")
    student_name: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool = True
    reply: str = Field(..., description="AI 回复内容")
    mode: str = Field(..., description="对话模式：deerflow/mock")
    can_extract_task: bool = False


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
