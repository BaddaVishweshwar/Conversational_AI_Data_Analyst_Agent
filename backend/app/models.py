from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Admin and 2FA fields
    is_admin = Column(Boolean, default=False)
    is_super_admin = Column(Boolean, default=False)  # Only for the main admin
    totp_secret = Column(String, nullable=True)  # For Google 2FA
    totp_enabled = Column(Boolean, default=False)
    
    # Relationships
    datasets = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    dashboards = relationship("Dashboard", back_populates="user", cascade="all, delete-orphan")
    connections = relationship("DataConnection", back_populates="user", cascade="all, delete-orphan")
    triggers = relationship("Trigger", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation model for multi-turn chat sessions"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    title = Column(String)  # Auto-generated from first query
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    dataset = relationship("Dataset", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """Message model for conversation messages"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)  # The actual message text
    
    # Query execution data (for assistant messages)
    query_data = Column(JSON)  # Stores SQL, results, visualization config, etc.
    processing_steps = Column(JSON)  # Steps shown during processing
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Dataset(Base):
    """Dataset model for uploaded files"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # csv, xlsx, xls
    row_count = Column(Integer)
    column_count = Column(Integer)
    schema = Column(JSON)  # Column names and types
    sample_data = Column(JSON)  # First few rows
    last_eda_report = Column(Text)  # Professional EDA findings
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("data_connections.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="completed") # processing, completed, error
    error_message = Column(Text)
    
    # Relationships
    owner = relationship("User", back_populates="datasets")
    connection = relationship("DataConnection", back_populates="datasets")
    queries = relationship("Query", back_populates="dataset", cascade="all, delete-orphan")
    triggers = relationship("Trigger", back_populates="dataset", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="dataset", cascade="all, delete-orphan")


class Query(Base):
    """Query model for storing query history"""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    natural_language_query = Column(Text, nullable=False)
    generated_sql = Column(Text)
    generated_code = Column(Text)
    result_data = Column(JSON)
    visualization_config = Column(JSON)  # Chart type, axes, etc.
    python_chart = Column(Text)  # Base64 encoded Matplotlib image
    analysis_strategy = Column(Text)
    execution_time = Column(Integer)  # milliseconds
    session_id = Column(String, index=True) # For grouping chat sessions
    insights = Column(Text)  # AI-generated analysis/insights
    status = Column(String)  # success, error, pending
    error_message = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # New multi-agent pipeline fields
    intent = Column(String)  # DESCRIPTIVE, DIAGNOSTIC, COMPARATIVE, TREND, PREDICTIVE, PRESCRIPTIVE
    analysis_plan = Column(JSON)  # Step-by-step analysis plan
    schema_analysis = Column(JSON)  # Schema metadata
    reasoning_steps = Column(JSON)  # Reasoning chain
    metrics_used = Column(JSON)  # All computed metrics
    
    # Relationships
    user = relationship("User", back_populates="queries")
    dataset = relationship("Dataset", back_populates="queries")


class Dashboard(Base):
    """Dashboard model for saved dashboards"""
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    layout = Column(JSON)  # Dashboard layout configuration
    widgets = Column(JSON)  # Array of widget configurations
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
# Relationships
    user = relationship("User", back_populates="dashboards")


class DataConnection(Base):
    """Database connections (Postgres, MySQL, Snowflake, etc)"""
    __tablename__ = "data_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # postgres, mysql, snowflake, sqlite
    host = Column(String)
    port = Column(Integer)
    database = Column(String)
    username = Column(String)
    password = Column(String)
    additional_params = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="connections")
    datasets = relationship("Dataset", back_populates="connection")


class Trigger(Base):
    """Automated data alerts and triggers"""
    __tablename__ = "triggers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    condition_sql = Column(Text, nullable=False) # SQL returning a single value
    operator = Column(String, nullable=False) # >, <, =, >=, <=
    threshold = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="triggers")
    dataset = relationship("Dataset", back_populates="triggers")


class AdminAuditLog(Base):
    """Audit log for admin actions"""
    __tablename__ = "admin_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # 'grant_admin', 'revoke_admin', 'login', etc.
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # User affected by action
    details = Column(JSON)  # Additional details about the action
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
