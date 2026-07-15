from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
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
