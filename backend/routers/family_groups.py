"""
Family Groups Router
Handles family learning groups and chat functionality
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os

from models.user import User, UserManager
from services.family_groups import FamilyGroupService
from services.emotion_ai import EmotionRecognitionAI
from services.email_service import send_family_group_invitation
from routers.auth import get_current_user

router = APIRouter(prefix="/api/family", tags=["family_groups"])

# Initialize services
family_service = FamilyGroupService(os.getenv("DB_PATH", "keliva.db"))
emotion_ai = EmotionRecognitionAI(os.getenv("DB_PATH", "keliva.db"))

class CreateFamilyGroup(BaseModel):
    name: str
    description: Optional[str] = None
    initial_members: Optional[List[str]] = []

class AddMember(BaseModel):
    user_id: str

class SendMessage(BaseModel):
    message_text: Optional[str] = None
    message_type: str = "text"  # text, image, file, system
    image_url: Optional[str] = None
    file_url: Optional[str] = None
    reply_to_message_id: Optional[str] = None

class UpdateGroupSettings(BaseModel):
    settings: Dict[str, Any]

@router.post("/groups")
async def create_family_group(
    group_data: CreateFamilyGroup,
    current_user: User = Depends(get_current_user)
):
    """Create a new family learning group"""
    group_id = family_service.create_family_group(
        name=group_data.name,
        description=group_data.description,
        created_by=current_user.id,
        initial_members=group_data.initial_members
    )
    
    if not group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create family group"
        )
    
    group = family_service.get_family_group(group_id)
    
    return {
        "message": "Family group created successfully",
        "group": group
    }

@router.get("/groups")
async def get_user_family_groups(current_user: User = Depends(get_current_user)):
    """Get all family groups for current user"""
    groups = family_service.get_user_family_groups(current_user.id)
    return {"groups": groups}

@router.get("/groups/{group_id}")
async def get_family_group(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get family group details"""
    group = family_service.get_family_group(group_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family group not found"
        )
    
    # Check if user is member
    member_ids = [member['id'] for member in group['members']]
    if current_user.id not in member_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    return {"group": group}

@router.post("/groups/{group_id}/members")
async def add_member_to_group(
    group_id: str,
    member_data: AddMember,
    current_user: User = Depends(get_current_user)
):
    """Add a member to family group"""
    success = family_service.add_member_to_group(
        group_id=group_id,
        user_id=member_data.user_id,
        added_by=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add member to group"
        )
    
    return {"message": "Member added successfully"}

@router.post("/groups/{group_id}/messages")
async def send_message(
    group_id: str,
    message_data: SendMessage,
    current_user: User = Depends(get_current_user)
):
    """Send a message to family group"""
    # Analyze emotion if text message
    emotion_detected = None
    if message_data.message_text and message_data.message_type == "text":
        emotion_analysis = emotion_ai.analyze_text_emotion(
            message_data.message_text, 
            current_user.id
        )
        emotion_detected = emotion_analysis.primary_emotion
    
    message_id = family_service.add_chat_message(
        group_id=group_id,
        sender_id=current_user.id,
        message_text=message_data.message_text,
        message_type=message_data.message_type,
        image_url=message_data.image_url,
        file_url=message_data.file_url,
        reply_to_message_id=message_data.reply_to_message_id,
        emotion_detected=emotion_detected
    )
    
    if not message_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send message"
        )
    
    return {
        "message": "Message sent successfully",
        "message_id": message_id,
        "emotion_detected": emotion_detected
    }

@router.get("/groups/{group_id}/messages")
async def get_group_messages(
    group_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get messages from family group"""
    # Verify user is group member
    group = family_service.get_family_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family group not found"
        )
    
    member_ids = [member['id'] for member in group['members']]
    if current_user.id not in member_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    messages = family_service.get_chat_messages(group_id, limit, offset)
    
    return {
        "messages": [msg.to_dict() for msg in messages],
        "total_count": len(messages)
    }

@router.put("/groups/{group_id}/settings")
async def update_group_settings(
    group_id: str,
    settings_data: UpdateGroupSettings,
    current_user: User = Depends(get_current_user)
):
    """Update family group settings"""
    success = family_service.update_group_settings(
        group_id=group_id,
        user_id=current_user.id,
        settings=settings_data.settings
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update group settings"
        )
    
    return {"message": "Group settings updated successfully"}





class InviteMember(BaseModel):
    email: str

@router.post("/groups/{group_id}/invite")
async def invite_member_to_group(
    group_id: str,
    invite_data: InviteMember,
    current_user: User = Depends(get_current_user)
):
    """Send invitation to join family group"""
    # Get group details for email
    group = family_service.get_family_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family group not found"
        )
    
    # Check if user is member of the group
    member_ids = [member['id'] for member in group['members']]
    if current_user.id not in member_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    # Create invitation
    invitation_data = family_service.create_group_invitation(
        group_id=group_id,
        invited_by=current_user.id,
        invited_email=invite_data.email
    )
    
    if not invitation_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create invitation"
        )
    
    invitation_id = invitation_data.get("invitation_id")
    invitation_code = invitation_data.get("invitation_code")
    
    # Send email invitation
    try:
        email_sent = await send_family_group_invitation(
            recipient_email=invite_data.email,
            invitation_id=invitation_id,
            group_id=group_id,
            group_name=group['name'],
            inviter_name=current_user.full_name or current_user.name or "A family member",
            invitation_code=invitation_code
        )
        
        # Create invitation link for sharing
        frontend_url = os.getenv("FRONTEND_URL", "https://keliva-app.pages.dev")
        invitation_link = f"{frontend_url}/join-family-group?code={invitation_code}&group={group_id}"
        
        if email_sent:
            return {
                "message": "Invitation created successfully! Share the code or link with the recipient.",
                "invitation_id": invitation_id,
                "invitation_code": invitation_code,
                "invitation_link": invitation_link,
                "email_sent": True,
                "instructions": f"The recipient can join by visiting {frontend_url} and entering the code: {invitation_code}"
            }
        else:
            return {
                "message": "Invitation created successfully! Share the code or link with the recipient.",
                "invitation_id": invitation_id,
                "invitation_code": invitation_code,
                "invitation_link": invitation_link,
                "email_sent": False,
                "instructions": f"Share this code with {invite_data.email}: {invitation_code}",
                "manual_email_template": f"""
Subject: You're invited to join '{group['name']}' on Keliva! 🎉

Hello!

{current_user.full_name or current_user.name or 'A family member'} has invited you to join the '{group['name']}' family learning group on Keliva.

🚀 JOIN NOW: {invitation_link}
🔑 OR USE CODE: {invitation_code}

Visit: https://keliva-app.pages.dev
                """.strip()
            }
    except Exception as e:
        # Create invitation link for sharing
        frontend_url = os.getenv("FRONTEND_URL", "https://keliva-app.pages.dev")
        invitation_link = f"{frontend_url}/join-family-group?code={invitation_code}&group={group_id}"
        
        return {
            "message": "Invitation created successfully! Share the code or link with the recipient.",
            "invitation_id": invitation_id,
            "invitation_code": invitation_code,
            "invitation_link": invitation_link,
            "email_sent": False,
            "instructions": f"Share this code with {invite_data.email}: {invitation_code}",
            "error": str(e)
        }

@router.get("/groups/{group_id}/progress")
async def get_group_learning_progress(
    group_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get learning progress for all group members"""
    # Verify user is group member
    group = family_service.get_family_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family group not found"
        )
    
    member_ids = [member['id'] for member in group['members']]
    if current_user.id not in member_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    activities = family_service.get_group_learning_activities(group_id)
    
    return {
        "activities": [activity.to_dict() for activity in activities],
        "total_count": len(activities)
    }

@router.post("/groups/{group_id}/activity")
async def create_learning_activity(
    group_id: str,
    activity_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a new learning activity for the group"""
    activity_id = family_service.create_learning_activity(
        group_id=group_id,
        created_by=current_user.id,
        activity_type=activity_data.get("activity_type", "general"),
        activity_data=activity_data
    )
    
    if not activity_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create learning activity"
        )
    
    return {
        "message": "Learning activity created successfully",
        "activity_id": activity_id
    }

@router.put("/groups/{group_id}/messages/{message_id}")
async def edit_message(
    group_id: str,
    message_id: str,
    message_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Edit a chat message"""
    success = family_service.edit_chat_message(
        message_id=message_id,
        user_id=current_user.id,
        new_text=message_data.get("message_text", "")
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to edit message"
        )
    
    return {"message": "Message edited successfully"}

@router.delete("/groups/{group_id}/messages/{message_id}")
async def delete_message(
    group_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a chat message"""
    success = family_service.delete_chat_message(
        message_id=message_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete message"
        )
    
    return {"message": "Message deleted successfully"}


class JoinByInvitation(BaseModel):
    invitation_code: str

@router.post("/join-by-invitation")
async def join_group_by_invitation(
    join_data: JoinByInvitation,
    current_user: User = Depends(get_current_user)
):
    """Join a family group using invitation code"""
    result = family_service.join_group_by_invitation(
        invitation_code=join_data.invitation_code,
        user_id=current_user.id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation code"
        )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return {
        "message": result["message"],
        "group_id": result["group_id"],
        "group_name": result["group_name"]
    }