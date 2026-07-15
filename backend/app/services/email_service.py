import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.enabled = settings.SMTP_ENABLED
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM or settings.SMTP_USER

    def send_welcome_email(self, to_email: str, student_name: str) -> bool:
        chat_url = f"{settings.FRONTEND_URL}/chat?email={quote(to_email)}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #1f2430; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .container {{ background: #f8f8fb; border-radius: 16px; padding: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ font-size: 28px; font-weight: 800; color: #1f6fe5; }}
                .greeting {{ font-size: 22px; font-weight: 600; margin-bottom: 20px; color: #12213f; }}
                .content {{ font-size: 16px; color: #4b5563; margin-bottom: 30px; }}
                .cta-button {{ display: inline-block; background: #1f6fe5; color: white !important; padding: 16px 40px; border-radius: 999px; text-decoration: none; font-weight: 600; font-size: 18px; }}
                .cta-wrap {{ text-align: center; margin: 30px 0; }}
                .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 14px; color: #9ca3af; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">Awaken™</div>
                </div>
                <div class="greeting">你好，{student_name}！</div>
                <div class="content">
                    <p>欢迎加入 Awaken，你的 AI 生涯成长伙伴。</p>
                    <p>我是「小海」，我会通过苏格拉底式的对话，帮你发现真正感兴趣的方向，并为你制定可执行的微行动任务。</p>
                    <p>点击下方按钮，开始我们的第一次对话吧：</p>
                </div>
                <div class="cta-wrap">
                    <a href="{chat_url}" class="cta-button">开始与小海对话</a>
                </div>
                <div class="footer">
                    <p>Awaken — AI 助你规划升学与职业未来</p>
                    <p>如果你没有注册过此账号，请忽略此邮件。</p>
                </div>
            </div>
        </body>
        </html>
        """

        if not self.enabled:
            logger.info(f"[MOCK] 欢迎邮件已发送至 {to_email}，对话链接: {chat_url}")
            return True

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"欢迎 {student_name}！开始你的 Awaken 成长之旅"
            message["From"] = self.smtp_from
            message["To"] = to_email

            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_from, to_email, message.as_string())

            logger.info(f"欢迎邮件已成功发送至 {to_email}")
            return True
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False


email_service = EmailService()
