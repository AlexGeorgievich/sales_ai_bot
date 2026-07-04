# Data access layer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime

from app.db.models import User, Dialog, Message, Lead, ClientType, LeadStatus
from app.utils.logger import logger


class UserRepository:
    """Репозиторий для работы с пользователями."""
    
    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        external_id: str,
        client_type: ClientType = ClientType.MSB
    ) -> User:
        """Получить пользователя по external_id или создать нового."""
        result = await session.execute(
            select(User).where(User.external_id == external_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(external_id=external_id, client_type=client_type)
            session.add(user)
            await session.flush()
            logger.info("New user created", external_id=external_id)
        
        return user


class DialogRepository:
    """Репозиторий для работы с диалогами."""
    
    @staticmethod
    async def create_dialog(
        session: AsyncSession,
        user_id: int,
        session_id: str
    ) -> Dialog:
        """Создать новый диалог."""
        dialog = Dialog(user_id=user_id, session_id=session_id)
        session.add(dialog)
        await session.flush()
        logger.info("Dialog created", session_id=session_id)
        return dialog
    
    @staticmethod
    async def get_dialog_by_session(
        session: AsyncSession,
        session_id: str
    ) -> Optional[Dialog]:
        """Получить диалог по session_id."""
        result = await session.execute(
            select(Dialog).where(Dialog.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def close_dialog(session: AsyncSession, dialog_id: int) -> None:
        """Закрыть диалог."""
        result = await session.execute(
            select(Dialog).where(Dialog.id == dialog_id)
        )
        dialog = result.scalar_one_or_none()
        if dialog:
            dialog.ended_at = datetime.utcnow()
            dialog.status = "closed"
            logger.info("Dialog closed", dialog_id=dialog_id)


class MessageRepository:
    """Репозиторий для работы с сообщениями."""
    
    @staticmethod
    async def save_message(
        session: AsyncSession,
        dialog_id: int,
        role: str,
        content: str,
        metadata: dict = None
    ) -> Message:
        """Сохранить сообщение в диалог."""
        message = Message(
            dialog_id=dialog_id,
            role=role,
            content=content,
            meta_data=metadata or {}
        )
        session.add(message)
        await session.flush()
        return message
    
    @staticmethod
    async def get_dialog_messages(
        session: AsyncSession,
        dialog_id: int,
        limit: int = 50
    ) -> List[Message]:
        """Получить историю сообщений диалога."""
        result = await session.execute(
            select(Message)
            .where(Message.dialog_id == dialog_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()


class LeadRepository:
    """Репозиторий для работы с лидами."""
    
    @staticmethod
    async def create_lead(
        session: AsyncSession,
        user_id: int,
        dialog_id: int = None,
        client_name: str = None,
        client_phone: str = None,
        client_email: str = None,
        interested_product: str = None,
        client_comment: str = None
    ) -> Lead:
        """Создать нового лида."""
        lead = Lead(
            user_id=user_id,
            dialog_id=dialog_id,
            client_name=client_name,
            client_phone=client_phone,
            client_email=client_email,
            interested_product=interested_product,
            client_comment=client_comment
        )
        session.add(lead)
        await session.flush()
        logger.info("Lead created", user_id=user_id, status=LeadStatus.NEW)
        return lead

    @staticmethod
    async def get_lead_by_dialog(session: AsyncSession, dialog_id: int) -> Optional[Lead]:
        """Получить лида по ID диалога."""
        result = await session.execute(
            select(Lead).where(Lead.dialog_id == dialog_id)
        )
        return result.scalars().first()

    @staticmethod
    async def update_lead(
        session: AsyncSession,
        lead_id: int,
        **kwargs
    ) -> Optional[Lead]:
        """Обновить данные существующего лида."""
        result = await session.execute(
            select(Lead).where(Lead.id == lead_id)
        )
        lead = result.scalars().first()
        if lead:
            for key, value in kwargs.items():
                if hasattr(lead, key) and value is not None:
                    setattr(lead, key, value)
            await session.flush()
            logger.info("Lead updated", lead_id=lead_id)
        return lead
        