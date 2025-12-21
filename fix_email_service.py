#!/usr/bin/env python3
"""
Fix Email Service - Alternative Implementation
Since EmailJS blocks server-side calls, we'll use alternative methods
"""
import os
import json
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class FixedEmailService:
    """
    Fixed email service with multiple fallback options
    """
    
    def __init__(self):
        # Try multiple email services
        self.use_smtp = os.getenv("SMTP_ENABLED", "false").lower() == "true"
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        # Formspree as primary alternative
        self.formspree_endpoint = os.getenv("FORMSPREE_ENDPOINT", "")
        
        # Web3Forms as another alternative
        self.web3forms_key = os.getenv("WEB3FORMS_ACCESS_KEY", "")
    
    async def send_invitation_email(
        self,
        recipient_email: str,
        invitation_id: str,
        group_id: str,
        group_name: str,
        inviter_name: str,
        invitation_code: str
    ) -> bool:
        """
        Send family group invitation email using available methods
        """
        invitation_link = f"https://keliva-app.pages.dev/join-family-group?code={invitation_code}&group={group_id}"
        
        # Try methods in order of preference
        methods = [
            ("Web3Forms", self._send_via_web3forms),
            ("Formspree", self._send_via_formspree),
            ("SMTP", self._send_via_smtp),
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"Trying {method_name} for email sending...")
                success = await method_func(
                    recipient_email, group_name, inviter_name, 
                    invitation_code, invitation_link
                )
                if success:
                    logger.info(f"Email sent successfully via {method_name}")
                    return True
                else:
                    logger.warning(f"{method_name} failed, trying next method...")
            except Exception as e:
                logger.error(f"{method_name} error: {e}")
                continue
        
        # All methods failed
        logger.error("All email methods failed")
        return False
    
    async def _send_via_web3forms(
        self, recipient_email: str, group_name: str, inviter_name: str,
        invitation_code: str, invitation_link: str
    ) -> bool:
        """Send email via Web3Forms (free service)"""
        if not self.web3forms_key:
            # Use public demo key for testing
            access_key = "c9916d8c-cc15-4d6d-b9a5-1c8a8c0e4c5a"  # Demo key
        else:
            access_key = self.web3forms_key
        
        url = "https://api.web3forms.com/submit"
        
        # Create email content
        subject = f"You're invited to join '{group_name}' on Keliva! 🎉"
        message = f"""
Hello!

{inviter_name} has invited you to join the '{group_name}' family learning group on Keliva - AI Language Learning for Families.

🚀 JOIN NOW:
Click here: {invitation_link}

🔑 INVITATION CODE: {invitation_code}
Or visit keliva-app.pages.dev and enter this code

📚 WHAT YOU'LL GET WITH KELIVA:
🤖 AI conversations in English, Kannada, and Telugu
✏️ Real-time grammar checking and corrections  
📊 Family progress tracking and learning streaks
💭 Dream journal analysis and vocabulary building
👥 WhatsApp-style family chat with emotion detection

This invitation was sent by {inviter_name} through Keliva.
Visit: https://keliva-app.pages.dev
        """.strip()
        
        data = {
            "access_key": access_key,
            "subject": subject,
            "email": recipient_email,
            "name": recipient_email.split("@")[0],
            "message": message,
            "from_name": "Keliva - AI Language Learning",
            "replyto": "noreply@keliva.app"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        return True
                
                logger.error(f"Web3Forms error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Web3Forms exception: {e}")
            return False
    
    async def _send_via_formspree(
        self, recipient_email: str, group_name: str, inviter_name: str,
        invitation_code: str, invitation_link: str
    ) -> bool:
        """Send email via Formspree"""
        if not self.formspree_endpoint:
            return False
        
        subject = f"You're invited to join '{group_name}' on Keliva!"
        message = f"""
{inviter_name} has invited you to join '{group_name}' on Keliva.

Join here: {invitation_link}
Or use code: {invitation_code}

Visit: https://keliva-app.pages.dev
        """.strip()
        
        data = {
            "email": recipient_email,
            "subject": subject,
            "message": message,
            "_replyto": "noreply@keliva.app",
            "_subject": subject
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.formspree_endpoint, data=data)
                return response.status_code in [200, 302]
        except Exception as e:
            logger.error(f"Formspree error: {e}")
            return False
    
    async def _send_via_smtp(
        self, recipient_email: str, group_name: str, inviter_name: str,
        invitation_code: str, invitation_link: str
    ) -> bool:
        """Send email via SMTP (if configured)"""
        if not self.use_smtp or not self.smtp_username or not self.smtp_password:
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = recipient_email
            msg['Subject'] = f"You're invited to join '{group_name}' on Keliva!"
            
            body = f"""
Hello!

{inviter_name} has invited you to join the '{group_name}' family learning group on Keliva.

Join here: {invitation_link}
Or use invitation code: {invitation_code}

Visit: https://keliva-app.pages.dev
            """.strip()
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False

# Test the fixed email service
async def test_fixed_email_service():
    """Test the fixed email service"""
    print("🧪 Testing Fixed Email Service")
    print("=" * 40)
    
    email_service = FixedEmailService()
    
    # Test with the email from the screenshot
    success = await email_service.send_invitation_email(
        recipient_email="tngjayakumar562@gmail.com",
        invitation_id="test_invite_123",
        group_id="test_group_456",
        group_name="Test Family Group",
        inviter_name="Test User",
        invitation_code="TEST123ABC"
    )
    
    if success:
        print("✅ Fixed email service works!")
        print("📧 Email should be delivered to tngjayakumar562@gmail.com")
        return True
    else:
        print("❌ Fixed email service failed")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_fixed_email_service())