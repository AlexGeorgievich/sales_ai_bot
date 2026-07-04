# SQLAlchemy models
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.db.session import Base


class ClientType(str, enum.Enum):
    """Тип клиента."""
    MSB = "msb"
    ENTERPRISE = "enterprise"


class LeadStatus(str, enum.Enum):
    """Статус лида."""
    NEW = "new"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class User(Base):
    """Модель пользователя (клиента)."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), unique=True, index=True, nullable=False)  # ID из виджета
    client_type = Column(Enum(ClientType), default=ClientType.MSB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    dialogs = relationship("Dialog", back_populates="user", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="user", cascade="all, delete-orphan")


class Dialog(Base):
    """Модель диалога (сессии общения)."""
    __tablename__ = "dialogs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="active")  # active, closed
    
    # Связи
    user = relationship("User", back_populates="dialogs")
    messages = relationship("Message", back_populates="dialog", cascade="all, delete-orphan")


class Message(Base):
    """Модель сообщения в диалоге."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    dialog_id = Column(Integer, ForeignKey("dialogs.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_data = Column(JSON, nullable=True)  # Дополнительные данные (токены, время ответа)
    
    # Связи
    dialog = relationship("Dialog", back_populates="messages")


class Lead(Base):
    """Модель квалифицированного лида."""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dialog_id = Column(Integer, ForeignKey("dialogs.id"), nullable=True)
    
    # Статус и данные
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    
    # Явные поля для сбора (требование рецензента)
    client_name = Column(String(100), nullable=True)
    client_phone = Column(String(50), nullable=True)
    client_email = Column(String(100), nullable=True)
    interested_product = Column(String(200), nullable=True)
    client_comment = Column(Text, nullable=True)
    
    # Метаданные
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="leads")
    