import resend
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # For demo, email service will be mocked
        # In production, set RESEND_API_KEY environment variable
        self.api_key = os.environ.get('RESEND_API_KEY')
        if self.api_key:
            resend.api_key = self.api_key
        self.sender_email = os.environ.get('SENDER_EMAIL', 'noreply@capractice.com')
        self.sender_name = os.environ.get('SENDER_NAME', 'CA Practice Pro')
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("Email service disabled - RESEND_API_KEY not set")
    
    def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a transactional email."""
        if not self.enabled:
            logger.info(f"[MOCK EMAIL] To: {to}, Subject: {subject}")
            return {
                "success": True,
                "message_id": "mock-email-id",
                "recipient": to,
                "mocked": True
            }
        
        try:
            from_address = f"{self.sender_name} <{self.sender_email}>"
            
            params = {
                "from": from_address,
                "to": to,
                "subject": subject,
                "html": html
            }
            
            if text:
                params["text"] = text
            
            email = resend.Emails.send(params)
            
            if hasattr(email, 'id') and email.id:
                logger.info(f"Email sent successfully to {to}")
                return {
                    "success": True,
                    "message_id": email.id,
                    "recipient": to
                }
            else:
                logger.error(f"Failed to send email to {to}")
                return {
                    "success": False,
                    "error": str(email),
                    "recipient": to
                }
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "recipient": to
            }
    
    def send_deadline_reminder(
        self,
        to: str,
        task_name: str,
        deadline: datetime,
        priority: str
    ) -> Dict[str, Any]:
        """Send deadline reminder email."""
        priority_colors = {
            "LOW": "#4CAF50",
            "MEDIUM": "#2196F3",
            "HIGH": "#FF9800",
            "URGENT": "#F44336"
        }
        
        color = priority_colors.get(priority, "#2196F3")
        deadline_str = deadline.strftime("%B %d, %Y at %I:%M %p")
        
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px;">
                        <h1 style="color: #0f172a; margin: 0;">Task Deadline Reminder</h1>
                    </div>
                    <div style="margin: 20px 0;">
                        <p>Hello,</p>
                        <p>This is a reminder for an upcoming deadline:</p>
                        <h2 style="color: #0f172a;">{task_name}</h2>
                        <div style="display: inline-block; padding: 8px 12px; background-color: {color}; color: white; border-radius: 3px; font-weight: bold; margin: 10px 0;">
                            {priority} PRIORITY
                        </div>
                        <p><strong>Deadline:</strong> {deadline_str}</p>
                        <p>Please ensure this task is completed by the deadline.</p>
                    </div>
                    <div style="border-top: 1px solid #ddd; padding-top: 20px; font-size: 12px; color: #666;">
                        <p>This is an automated message from CA Practice Pro.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(
            to=to,
            subject=f"[{priority}] Deadline Reminder: {task_name}",
            html=html
        )
    
    def send_task_assignment(
        self,
        to: str,
        task_title: str,
        task_description: str,
        assigned_by: str
    ) -> Dict[str, Any]:
        """Send task assignment notification."""
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #10b981; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                        <h1 style="margin: 0;">New Task Assigned</h1>
                    </div>
                    <div style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #10b981;">
                        <p>Hello,</p>
                        <p>You have been assigned a new task by {assigned_by}:</p>
                        <h3 style="color: #0f172a;">{task_title}</h3>
                        <p>{task_description}</p>
                    </div>
                    <div style="background-color: #f5f5f5; padding: 20px; border-radius: 0 0 5px 5px; font-size: 12px; color: #666;">
                        <p>Log in to CA Practice Pro to view details.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(
            to=to,
            subject=f"New Task: {task_title}",
            html=html
        )

# Global email service instance
email_service = EmailService()