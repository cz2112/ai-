from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.upload import Upload
from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, ConversationResponse
from app.services.ai_service import chat_with_context

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/{upload_id}", response_model=ChatMessageResponse)
def send_message(
    upload_id: int,
    data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if not upload.transcript:
        raise HTTPException(status_code=400, detail="Upload has no transcript yet")

    # Get or create conversation
    if data.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == data.conversation_id,
            Conversation.user_id == current_user.id,
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = Conversation(user_id=current_user.id, upload_id=upload_id, title=data.message[:50])
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save user message
    user_msg = Message(conversation_id=conv.id, role="user", content=data.message)
    db.add(user_msg)
    db.commit()

    # Build message history for AI
    history = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
    ai_messages = [{"role": m.role, "content": m.content} for m in history]

    # Call AI
    response_text = chat_with_context(ai_messages, upload.transcript, lang=upload.language or "en")

    # Save assistant message
    assistant_msg = Message(conversation_id=conv.id, role="assistant", content=response_text)
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg


@router.get("/{upload_id}/conversations", response_model=list[ConversationResponse])
def list_conversations(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    convs = db.query(Conversation).filter(
        Conversation.upload_id == upload_id,
        Conversation.user_id == current_user.id,
    ).order_by(Conversation.created_at.desc()).all()
    return convs


@router.get("/{upload_id}/conversations/{conv_id}", response_model=ConversationResponse)
def get_conversation(
    upload_id: int,
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.upload_id == upload_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/{upload_id}/conversations/{conv_id}")
def delete_conversation(
    upload_id: int,
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.upload_id == upload_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"detail": "Conversation deleted"}
