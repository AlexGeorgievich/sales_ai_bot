from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.core.gigachat_service import gigachat_service
from app.db.session import get_db_session
from app.db.repository import UserRepository, DialogRepository, MessageRepository
from app.db.models import ClientType
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)
    client_type: str = Field(default="msb", pattern="^(msb|enterprise)$")
    session_id: Optional[str] = None  # Если None — создаем новую сессию


class ChatResponse(BaseModel):
    user_id: str
    session_id: str
    response: str
    client_type: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


@router.post("/message", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_message(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Основной endpoint для общения с ботом.
    Сохраняет историю диалога в БД.
    """
    logger.info(
        "Processing chat message",
        user_id=request.user_id,
        client_type=request.client_type
    )
    
    try:
        # Получаем или создаем пользователя
        user = await UserRepository.get_or_create_user(
            session=session,
            external_id=request.user_id,
            client_type=ClientType(request.client_type)
        )
        
        # Получаем или создаем диалог
        session_id = request.session_id or str(uuid.uuid4())
        dialog = await DialogRepository.get_dialog_by_session(session, session_id)
        
        if not dialog:
            dialog = await DialogRepository.create_dialog(
                session=session,
                user_id=user.id,
                session_id=session_id
            )
        
        # Сохраняем сообщение пользователя
        await MessageRepository.save_message(
            session=session,
            dialog_id=dialog.id,
            role="user",
            content=request.message
        )
        
        # Получаем историю диалога для контекста
        messages = await MessageRepository.get_dialog_messages(
            session=session,
            dialog_id=dialog.id,
            limit=20  # Последние 20 сообщений
        )
        
        # Формируем историю для GigaChat (без текущего сообщения)
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[:-1]  # Исключаем последнее (текущее)
        ]
        
        # Генерируем ответ
        response_text = await gigachat_service.generate_response(
            user_message=request.message,
            conversation_history=history,
            client_type=request.client_type
        )
        
        # Сохраняем ответ бота
        await MessageRepository.save_message(
            session=session,
            dialog_id=dialog.id,
            role="assistant",
            content=response_text,
            metadata={"tokens_used": len(response_text.split())}
        )
        
        # Если в ответе содержится фраза о принятии заявки (со сбором всех полей)
        lower_response = response_text.lower()
        if "заявка принята" in lower_response or "заявка получена" in lower_response or "заявка оформлена" in lower_response or "заявку принял" in lower_response:
            try:
                # Получаем полную историю диалога для экстракции
                full_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ]
                # Добавляем последний ответ ассистента в историю
                full_history.append({"role": "assistant", "content": response_text})
                
                # Экстрагируем данные лида
                lead_data = await gigachat_service.extract_lead_info(full_history)
                if lead_data:
                    from app.db.repository import LeadRepository
                    
                    # Проверяем, существует ли уже лид для этого диалога
                    existing_lead = await LeadRepository.get_lead_by_dialog(session, dialog.id)
                    if existing_lead:
                        # Обновляем существующий лид
                        await LeadRepository.update_lead(
                            session=session,
                            lead_id=existing_lead.id,
                            client_name=lead_data.get("name"),
                            client_phone=lead_data.get("phone"),
                            client_email=lead_data.get("email"),
                            interested_product=lead_data.get("product"),
                            client_comment=lead_data.get("comment")
                        )
                        logger.info("Lead successfully updated in DB", user_id=user.id, lead_id=existing_lead.id)
                    else:
                        # Создаем новый лид
                        await LeadRepository.create_lead(
                            session=session,
                            user_id=user.id,
                            dialog_id=dialog.id,
                            client_name=lead_data.get("name"),
                            client_phone=lead_data.get("phone"),
                            client_email=lead_data.get("email"),
                            interested_product=lead_data.get("product"),
                            client_comment=lead_data.get("comment")
                        )
                        logger.info("Lead successfully saved to DB", user_id=user.id)
            except Exception as e:
                logger.error("Failed to save lead in chat endpoint", error=str(e), exc_info=True)
        
        return ChatResponse(
            user_id=request.user_id,
            session_id=session_id,
            response=response_text,
            client_type=request.client_type,
            timestamp=datetime.utcnow(),
            metadata={
                "dialog_id": dialog.id,
                "messages_count": len(messages) + 1
            }
        )
    
    except Exception as e:
        logger.error(
            "Failed to process chat message",
            user_id=request.user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.get("/history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(
    session_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Получение истории диалога по session_id."""
    dialog = await DialogRepository.get_dialog_by_session(session, session_id)
    
    if not dialog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dialog not found"
        )
    
    messages = await MessageRepository.get_dialog_messages(
        session=session,
        dialog_id=dialog.id
    )
    
    return [
        ChatMessage(role=msg.role, content=msg.content)
        for msg in messages
    ]