from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.conversation import ChatMessage, Conversation
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, ConversationResponse
from app.services.ai_service import chat_with_context
from app.services.upload_access import require_upload_read_access


router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_accessible_upload(db: Session, upload_id: int, user_id: int):
    upload = require_upload_read_access(db, upload_id, user_id)
    if not upload.transcript:
        raise HTTPException(status_code=400, detail="Upload has no transcript yet")
    return upload


def _conversation_query(db: Session, upload_id: int, user_id: int):
    return (
        db.query(Conversation)
        .options(joinedload(Conversation.messages))
        .filter(Conversation.upload_id == upload_id, Conversation.user_id == user_id)
    )


@router.post("/{upload_id}", response_model=ChatMessageResponse)
def send_message(
    upload_id: int,
    data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = _get_accessible_upload(db, upload_id, current_user.id)

    content = data.message.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    conversation = None
    if data.conversation_id is not None:
        conversation = _conversation_query(db, upload_id, current_user.id).filter(
            Conversation.id == data.conversation_id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        title = content[:60] + ("..." if len(content) > 60 else "")
        conversation = Conversation(
            upload_id=upload_id,
            user_id=current_user.id,
            title=title or "New Conversation",
        )
        db.add(conversation)
        db.flush()

    user_message = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=content,
    )
    db.add(user_message)
    db.flush()

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .all()
    )
    ai_reply = chat_with_context(
        [{"role": message.role, "content": message.content} for message in history],
        upload.transcript,
        lang=upload.language or "en",
    )

    assistant_message = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_reply,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message


@router.get("/{upload_id}/conversations", response_model=list[ConversationResponse])
def list_conversations(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_accessible_upload(db, upload_id, current_user.id)
    return _conversation_query(db, upload_id, current_user.id).order_by(Conversation.created_at.desc()).all()


@router.get("/{upload_id}/conversations/{conv_id}", response_model=ConversationResponse)
def get_conversation(
    upload_id: int,
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_accessible_upload(db, upload_id, current_user.id)
    conversation = _conversation_query(db, upload_id, current_user.id).filter(Conversation.id == conv_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{upload_id}/conversations/{conv_id}")
def delete_conversation(
    upload_id: int,
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_accessible_upload(db, upload_id, current_user.id)
    conversation = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.upload_id == upload_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()
    return {"detail": "Conversation deleted"}
