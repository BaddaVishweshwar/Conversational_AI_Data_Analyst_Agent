"""
Conversation Service - Manages multi-turn chat sessions

Handles conversation context, message history, and context resolution
for conversational NLP queries.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import Conversation, Message, Dataset, User
from ..database import get_db


class ConversationService:
    """Service for managing conversations and context"""
    
    def create_conversation(
        self,
        db: Session,
        user_id: int,
        dataset_id: int,
        initial_query: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation"""
        # Generate title from first query or use default
        title = self._generate_title(initial_query) if initial_query else "New Conversation"
        
        conversation = Conversation(
            user_id=user_id,
            dataset_id=dataset_id,
            title=title
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    def get_conversation(
        self,
        db: Session,
        conversation_id: int,
        user_id: int
    ) -> Optional[Conversation]:
        """Get a conversation by ID (with user ownership check)"""
        return db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
    
    def get_user_conversations(
        self,
        db: Session,
        user_id: int,
        dataset_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Conversation]:
        """Get all conversations for a user"""
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        
        if dataset_id:
            query = query.filter(Conversation.dataset_id == dataset_id)
        
        return query.order_by(Conversation.updated_at.desc()).limit(limit).all()
    
    def add_message(
        self,
        db: Session,
        conversation_id: int,
        role: str,  # 'user' or 'assistant'
        content: str,
        query_data: Optional[Dict[str, Any]] = None,
        processing_steps: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        """Add a message to a conversation"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            query_data=query_data,
            processing_steps=processing_steps
        )
        db.add(message)
        
        # Update conversation's updated_at timestamp
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        return message
    
    def get_conversation_history(
        self,
        db: Session,
        conversation_id: int,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get message history for a conversation"""
        query = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_last_assistant_message(
        self,
        db: Session,
        conversation_id: int
    ) -> Optional[Message]:
        """Get the last assistant message (for context)"""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == 'assistant'
        ).order_by(Message.created_at.desc()).first()
    
    def get_conversation_context(
        self,
        db: Session,
        conversation_id: int,
        max_messages: int = 10
    ) -> Dict[str, Any]:
        """
        Get conversation context for query resolution
        
        Returns:
            {
                'messages': [...],  # Recent messages
                'last_query': str,  # Last user query
                'last_result': dict,  # Last query result
                'last_sql': str,  # Last generated SQL
                'dataset_id': int
            }
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            return {}
        
        # Get recent messages
        messages = self.get_conversation_history(db, conversation_id, limit=max_messages)
        
        # Extract last query and result
        last_query = None
        last_result = None
        last_sql = None
        
        for message in reversed(messages):
            if message.role == 'user' and not last_query:
                last_query = message.content
            elif message.role == 'assistant' and message.query_data:
                last_result = message.query_data.get('result_data')
                last_sql = message.query_data.get('generated_sql')
                if last_query:  # Found both
                    break
        
        return {
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'query_data': msg.query_data
                }
                for msg in messages
            ],
            'last_query': last_query,
            'last_result': last_result,
            'last_sql': last_sql,
            'dataset_id': conversation.dataset_id
        }
    
    def delete_conversation(
        self,
        db: Session,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """Delete a conversation (with user ownership check)"""
        conversation = self.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return False
        
        db.delete(conversation)
        db.commit()
        return True
    
    def _generate_title(self, query: str, max_length: int = 50) -> str:
        """Generate a conversation title from the first query"""
        if len(query) <= max_length:
            return query
        return query[:max_length - 3] + "..."


# Singleton instance
conversation_service = ConversationService()
