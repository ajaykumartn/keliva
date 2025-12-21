"""
Family Learning Groups Service
Handles family group creation, management, and communication
"""
import secrets
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class FamilyChatMessage:
    id: str
    family_group_id: str
    sender_id: str
    sender_name: str
    message_text: Optional[str]
    message_type: str  # 'text', 'image', 'file', 'system'
    image_url: Optional[str]
    file_url: Optional[str]
    emotion_detected: Optional[str]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'family_group_id': self.family_group_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender_name,
            'message_text': self.message_text,
            'message_type': self.message_type,
            'image_url': self.image_url,
            'file_url': self.file_url,
            'emotion_detected': self.emotion_detected,
            'created_at': self.created_at.isoformat()
        }

class FamilyGroupService:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def create_family_group(self, name: str, created_by: str, description: str = None, initial_members: List[str] = None) -> Optional[str]:
        """Create a new family group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            group_id = f"family_{secrets.token_urlsafe(12)}"
            members = initial_members or [created_by]
            if created_by not in members:
                members.append(created_by)
            
            group_settings = {
                'emotion_detection': True,
                'learning_reminders': True,
                'shared_vocabulary': True,
                'progress_sharing': True
            }
            
            cursor.execute('''
                INSERT INTO family_groups (id, name, description, created_by, members, group_settings)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (group_id, name, description, created_by, json.dumps(members), json.dumps(group_settings)))
            
            # Update all members' family_group_id
            for member_id in members:
                cursor.execute('''
                    UPDATE users SET family_group_id = ? WHERE id = ?
                ''', (group_id, member_id))
            
            conn.commit()
            return group_id
            
        except Exception as e:
            print(f"Error creating family group: {e}")
            return None
        finally:
            conn.close()
    
    def get_family_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """Get family group details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fg.id, fg.name, fg.description, fg.created_by, fg.created_at, 
                   fg.members, fg.group_settings, fg.is_active, fg.group_avatar, 
                   u.full_name as creator_name
            FROM family_groups fg
            LEFT JOIN users u ON fg.created_by = u.id
            WHERE fg.id = ? AND fg.is_active = 1
        ''', (group_id,))
        
        row = cursor.fetchone()
        
        if row:
            members = json.loads(row[5]) if row[5] else []
            
            # Get member details
            member_details = []
            for member_id in members:
                cursor.execute('''
                    SELECT id, name, full_name, profile_picture, last_login, 
                           learning_streak, total_points
                    FROM users WHERE id = ?
                ''', (member_id,))
                member_row = cursor.fetchone()
                if member_row:
                    member_details.append({
                        'id': member_row[0],
                        'name': member_row[1] or member_row[2] or 'Unknown',
                        'full_name': member_row[2] or member_row[1] or 'Unknown',
                        'profile_picture': member_row[3],
                        'last_login': member_row[4],
                        'learning_streak': member_row[5] or 0,
                        'total_points': member_row[6] or 0,
                        'is_online': self._is_user_online(member_row[4]),
                        'role': 'admin' if member_row[0] == row[3] else 'member'
                    })
            
            conn.close()
            
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'created_by': row[3],
                'creator_name': row[9] or 'Unknown',
                'created_at': row[4],
                'members': member_details,
                'group_settings': json.loads(row[6]) if row[6] else {},
                'is_active': bool(row[7]),
                'group_avatar': row[8]
            }
        
        conn.close()
        return None
    
    def add_member_to_group(self, group_id: str, user_id: str, added_by: str) -> bool:
        """Add a member to family group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user adding is group member
            cursor.execute('''
                SELECT members FROM family_groups WHERE id = ? AND is_active = 1
            ''', (group_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            current_members = json.loads(row[0])
            if added_by not in current_members:
                return False
            
            # Add new member
            if user_id not in current_members:
                current_members.append(user_id)
                
                cursor.execute('''
                    UPDATE family_groups SET members = ? WHERE id = ?
                ''', (json.dumps(current_members), group_id))
                
                cursor.execute('''
                    UPDATE users SET family_group_id = ? WHERE id = ?
                ''', (group_id, user_id))
                
                conn.commit()
                
                # Add system message
                self.add_chat_message(
                    group_id, 
                    "system", 
                    f"New member joined the family group!",
                    message_type="system"
                )
                
            return True
            
        except Exception as e:
            print(f"Error adding member: {e}")
            return False
        finally:
            conn.close()
    
    def add_chat_message(self, group_id: str, sender_id: str, message_text: str = None, 
                        message_type: str = "text", image_url: str = None, file_url: str = None,
                        reply_to_message_id: str = None, emotion_detected: str = None) -> Optional[str]:
        """Add a chat message to family group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            message_id = f"msg_{secrets.token_urlsafe(12)}"
            
            cursor.execute('''
                INSERT INTO family_chat_messages 
                (id, family_group_id, sender_id, message_text, message_type, 
                 image_url, file_url, reply_to_message_id, emotion_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, group_id, sender_id, message_text, message_type, 
                  image_url, file_url, reply_to_message_id, emotion_detected))
            
            conn.commit()
            return message_id
            
        except Exception as e:
            print(f"Error adding chat message: {e}")
            return None
        finally:
            conn.close()
    
    def get_chat_messages(self, group_id: str, limit: int = 50, offset: int = 0) -> List[FamilyChatMessage]:
        """Get chat messages for family group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fcm.*, u.full_name as sender_name
            FROM family_chat_messages fcm
            LEFT JOIN users u ON fcm.sender_id = u.id
            WHERE fcm.family_group_id = ?
            ORDER BY fcm.created_at DESC
            LIMIT ? OFFSET ?
        ''', (group_id, limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            # Handle datetime parsing safely
            try:
                created_at = datetime.fromisoformat(row[8]) if row[8] else datetime.now()
            except (ValueError, TypeError):
                created_at = datetime.now()
            
            messages.append(FamilyChatMessage(
                id=row[0],
                family_group_id=row[1],
                sender_id=row[2],
                sender_name=row[9] or "System",
                message_text=row[3],
                message_type=row[4],
                image_url=row[5],
                file_url=row[6],
                emotion_detected=row[7],
                created_at=created_at
            ))
        
        return messages
    
    def get_user_family_groups(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all family groups for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fg.*, u.full_name as creator_name
            FROM family_groups fg
            JOIN users u ON fg.created_by = u.id
            WHERE fg.is_active = 1 AND json_extract(fg.members, '$') LIKE ?
        ''', (f'%"{user_id}"%',))
        
        rows = cursor.fetchall()
        conn.close()
        
        groups = []
        for row in rows:
            groups.append({
                'id': row[0],
                'name': row[1],
                'created_by': row[2],
                'creator_name': row[7],
                'created_at': row[3],
                'member_count': len(json.loads(row[4])),
                'group_settings': json.loads(row[5])
            })
        
        return groups
    
    def _is_user_online(self, last_login: str) -> bool:
        """Check if user is considered online (logged in within last 5 minutes)"""
        if not last_login:
            return False
        
        try:
            last_login_dt = datetime.fromisoformat(last_login)
            return (datetime.now() - last_login_dt).total_seconds() < 300  # 5 minutes
        except:
            return False
    
    def update_group_settings(self, group_id: str, user_id: str, settings: Dict[str, Any]) -> bool:
        """Update family group settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user is group member
            cursor.execute('''
                SELECT members FROM family_groups WHERE id = ? AND is_active = 1
            ''', (group_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            members = json.loads(row[0])
            if user_id not in members:
                return False
            
            cursor.execute('''
                UPDATE family_groups SET group_settings = ? WHERE id = ?
            ''', (json.dumps(settings), group_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating group settings: {e}")
            return False
        finally:
            conn.close()
    
    def create_group_invitation(self, group_id: str, invited_by: str, invited_email: str) -> Optional[Dict[str, str]]:
        """Create an invitation to join family group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            invitation_id = f"invite_{secrets.token_urlsafe(12)}"
            invitation_code = secrets.token_urlsafe(16)
            
            # Set expiration to 7 days from now
            from datetime import datetime, timedelta
            expires_at = (datetime.now() + timedelta(days=7)).isoformat()
            
            cursor.execute('''
                INSERT INTO family_group_invitations 
                (id, group_id, invited_by, invited_user_email, invitation_code, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (invitation_id, group_id, invited_by, invited_email, invitation_code, expires_at))
            
            conn.commit()
            return {
                "invitation_id": invitation_id,
                "invitation_code": invitation_code,
                "expires_at": expires_at
            }
            
        except Exception as e:
            print(f"Error creating invitation: {e}")
            return None
        finally:
            conn.close()
    
    def join_group_by_invitation(self, invitation_code: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Join a family group using invitation code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Find valid invitation
            cursor.execute('''
                SELECT fgi.*, fg.name as group_name
                FROM family_group_invitations fgi
                JOIN family_groups fg ON fgi.group_id = fg.id
                WHERE fgi.invitation_code = ? 
                AND fgi.is_used = 0 
                AND fgi.expires_at > datetime('now')
                AND fg.is_active = 1
            ''', (invitation_code,))
            
            invitation = cursor.fetchone()
            if not invitation:
                return None
            
            group_id = invitation[1]  # group_id column
            
            # Check if user is already a member
            cursor.execute('''
                SELECT members FROM family_groups WHERE id = ?
            ''', (group_id,))
            
            group_row = cursor.fetchone()
            if not group_row:
                return None
            
            current_members = json.loads(group_row[0])
            if user_id in current_members:
                return {"error": "User is already a member of this group"}
            
            # Add user to group
            current_members.append(user_id)
            cursor.execute('''
                UPDATE family_groups SET members = ? WHERE id = ?
            ''', (json.dumps(current_members), group_id))
            
            # Update user's family_group_id
            cursor.execute('''
                UPDATE users SET family_group_id = ? WHERE id = ?
            ''', (group_id, user_id))
            
            # Mark invitation as used
            cursor.execute('''
                UPDATE family_group_invitations 
                SET is_used = 1, used_at = CURRENT_TIMESTAMP, used_by = ?
                WHERE invitation_code = ?
            ''', (user_id, invitation_code))
            
            conn.commit()
            
            # Add system message
            self.add_chat_message(
                group_id, 
                "system", 
                f"New member joined the family group using invitation!",
                message_type="system"
            )
            
            return {
                "group_id": group_id,
                "group_name": invitation[7],  # group_name from JOIN
                "message": "Successfully joined the family group!"
            }
            
        except Exception as e:
            print(f"Error joining group by invitation: {e}")
            return None
        finally:
            conn.close()
    
    def get_group_learning_activities(self, group_id: str) -> List[Dict[str, Any]]:
        """Get learning activities for family group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT flp.*, u.full_name as user_name
            FROM family_learning_progress flp
            JOIN users u ON flp.user_id = u.id
            WHERE flp.group_id = ?
            ORDER BY flp.created_at DESC
            LIMIT 50
        ''', (group_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        activities = []
        for row in rows:
            activities.append({
                'id': row[0],
                'user_id': row[1],
                'user_name': row[7],
                'group_id': row[2],
                'activity_type': row[3],
                'progress_data': json.loads(row[4]) if row[4] else {},
                'points_earned': row[5],
                'created_at': row[6]
            })
        
        return activities
    
    def create_learning_activity(self, group_id: str, created_by: str, activity_type: str, activity_data: Dict[str, Any]) -> Optional[str]:
        """Create a learning activity for the group"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            activity_id = f"activity_{secrets.token_urlsafe(12)}"
            points_earned = activity_data.get('points', 10)  # Default 10 points
            
            cursor.execute('''
                INSERT INTO family_learning_progress 
                (id, user_id, group_id, activity_type, progress_data, points_earned)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (activity_id, created_by, group_id, activity_type, 
                  json.dumps(activity_data), points_earned))
            
            # Update user's total points
            cursor.execute('''
                UPDATE users SET total_points = total_points + ? WHERE id = ?
            ''', (points_earned, created_by))
            
            conn.commit()
            return activity_id
            
        except Exception as e:
            print(f"Error creating learning activity: {e}")
            return None
        finally:
            conn.close()
    
    def edit_chat_message(self, message_id: str, user_id: str, new_text: str) -> bool:
        """Edit a chat message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user owns the message
            cursor.execute('''
                SELECT sender_id FROM family_chat_messages WHERE id = ?
            ''', (message_id,))
            
            row = cursor.fetchone()
            if not row or row[0] != user_id:
                return False
            
            cursor.execute('''
                UPDATE family_chat_messages 
                SET message_text = ?, is_edited = 1, edited_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_text, message_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error editing message: {e}")
            return False
        finally:
            conn.close()
    
    def delete_chat_message(self, message_id: str, user_id: str) -> bool:
        """Delete a chat message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if user owns the message
            cursor.execute('''
                SELECT sender_id FROM family_chat_messages WHERE id = ?
            ''', (message_id,))
            
            row = cursor.fetchone()
            if not row or row[0] != user_id:
                return False
            
            cursor.execute('''
                DELETE FROM family_chat_messages WHERE id = ?
            ''', (message_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error deleting message: {e}")
            return False
        finally:
            conn.close()