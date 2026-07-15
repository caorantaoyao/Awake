import httpx
import json
from app.core.config import settings
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class FeishuService:
    def __init__(self):
        self.enabled = settings.FEISHU_ENABLED
        self.webhook_register = settings.FEISHU_WEBHOOK_REGISTER
        self.webhook_task_complete = settings.FEISHU_WEBHOOK_TASK_COMPLETE

    async def _send_webhook(self, url: str, payload: Dict[str, Any]) -> bool:
        if not self.enabled or not url:
            logger.info(f"[MOCK] 飞书 Webhook 调用: {url}, payload: {json.dumps(payload, ensure_ascii=False, default=str)}")
            return True

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"飞书 Webhook 调用成功: {url}")
                return True
        except Exception as e:
            logger.error(f"飞书 Webhook 调用失败: {e}")
            return False

    async def notify_new_student(self, student_data: Dict[str, Any]) -> bool:
        payload = {
            "msg_type": "event",
            "event_type": "new_student_registered",
            "data": {
                "name": student_data.get("name"),
                "email": student_data.get("email"),
                "grade": student_data.get("grade"),
                "registered_at": datetime.now().isoformat(),
                "operation_log": datetime.now().isoformat()
            }
        }
        return await self._send_webhook(self.webhook_register, payload)

    async def notify_task_complete(self, task_data: Dict[str, Any], student_data: Dict[str, Any]) -> bool:
        payload = {
            "msg_type": "event",
            "event_type": "task_completed",
            "data": {
                "task_id": task_data.get("id"),
                "task_description": task_data.get("description"),
                "student_name": student_data.get("name"),
                "student_email": student_data.get("email"),
                "feedback": task_data.get("feedback"),
                "completed_at": datetime.now().isoformat(),
                "operation_log": datetime.now().isoformat()
            }
        }
        return await self._send_webhook(self.webhook_task_complete, payload)

    async def notify_task_created(self, task_data: Dict[str, Any], student_data: Dict[str, Any]) -> bool:
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "🎯 新的微行动任务已生成"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**{student_data.get('name')}**，这是为你定制的微行动任务：\n\n{task_data.get('description')}"
                        }
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {
                                    "tag": "plain_text",
                                    "content": "完成打卡"
                                },
                                "type": "primary",
                                "url": f"{settings.FRONTEND_URL}/checkin?task_id={task_data.get('id')}"
                            }
                        ]
                    }
                ]
            }
        }
        logger.info(f"[MOCK] 任务卡片已生成: {json.dumps(payload, ensure_ascii=False, default=str)}")
        return True


feishu_service = FeishuService()
