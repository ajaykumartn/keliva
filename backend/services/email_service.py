"""
Email Service for Family Groups Invitations
Simple invitation code system - no external email service required
"""
import os
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """
    Simple email service that provides invitation codes for manual sharing
    No external dependencies or configuration required
    """
    
    def __init__(self):
        # Always use fallback mode - no external email service
        self.use_fallback = True
    
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
        Create invitation code for manual sharing
        
        Args:
            recipient_email: Email address to send invitation to
            invitation_id: Unique invitation ID
            group_id: Family group ID
            group_name: Name of the family group
            inviter_name: Name of person sending invitation
            invitation_code: Invitation code for joining
            
        Returns:
            True (always succeeds with manual code sharing)
        """
        try:
            return await self._create_manual_invitation(
                recipient_email, group_name, inviter_name, invitation_code
            )
        except Exception as e:
            logger.error(f"Failed to create invitation: {e}")
            return False
    
    async def _create_manual_invitation(
        self,
        recipient_email: str,
        group_name: str,
        inviter_name: str,
        invitation_code: str
    ) -> bool:
        """
        Create invitation code for manual sharing
        """
        try:
            # Create invitation link
            base_url = os.getenv("FRONTEND_URL", "https://keliva-app.pages.dev")
            invitation_link = f"{base_url}/join-family-group?code={invitation_code}&group=family_group"
            
            # Log invitation details for manual sharing
            logger.info("=" * 60)
            logger.info("📧 INVITATION CODE CREATED")
            logger.info("=" * 60)
            logger.info(f"👤 Recipient: {recipient_email}")
            logger.info(f"👥 Group: {group_name}")
            logger.info(f"👨‍💼 Inviter: {inviter_name}")
            logger.info(f"🔑 Invitation Code: {invitation_code}")
            logger.info(f"🔗 Join Link: {invitation_link}")
            logger.info("=" * 60)
            logger.info("📋 SHARE THIS WITH THE RECIPIENT:")
            logger.info("=" * 60)
            
            share_message = f"""
🎉 You're invited to join '{group_name}' on Keliva!

Hello!

{inviter_name} has invited you to join the '{group_name}' family learning group on Keliva - AI Language Learning for Families.

🚀 JOIN NOW:
Visit: {invitation_link}

🔑 INVITATION CODE: {invitation_code}

📚 WHAT YOU'LL GET WITH KELIVA:
🤖 AI conversations in English, Kannada, and Telugu
✏️ Real-time grammar checking and corrections  
📊 Family progress tracking and learning streaks
💭 Dream journal analysis and vocabulary building
👥 WhatsApp-style family chat with emotion detection

🎯 HOW TO JOIN:
1. Visit https://keliva-app.pages.dev
2. Create your free account or log in
3. Go to Family Groups
4. Click "Join Group" and enter code: {invitation_code}

This invitation was sent by {inviter_name} through Keliva.
Visit: https://keliva-app.pages.dev

Best regards,
The Keliva Team
            """.strip()
            
            logger.info(share_message)
            logger.info("=" * 60)
            
            # Always return True since we're providing the invitation code
            return True
                    
        except Exception as e:
            logger.error(f"Manual invitation creation failed: {e}")
            return False


# Create global email service instance
email_service = EmailService()


async def send_family_group_invitation(
    recipient_email: str,
    invitation_id: str,
    group_id: str,
    group_name: str,
    inviter_name: str,
    invitation_code: str
) -> bool:
    """
    Convenience function to create family group invitation code
    
    Args:
        recipient_email: Email address to send invitation to
        invitation_id: Unique invitation ID
        group_id: Family group ID
        group_name: Name of the family group
        inviter_name: Name of person sending invitation
        invitation_code: Invitation code for joining
        
    Returns:
        True (always succeeds with manual code sharing)
    """
    return await email_service.send_invitation_email(
        recipient_email=recipient_email,
        invitation_id=invitation_id,
        group_id=group_id,
        group_name=group_name,
        inviter_name=inviter_name,
        invitation_code=invitation_code
    )