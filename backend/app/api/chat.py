from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.upload import Upload
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

    # 临时禁用聊天功能，因为没有 conversation 模型
    raise HTTPException(status_code=501, detail="Chat functionality temporarily disabled")


@router.get("/{upload_id}/conversations", response_model=list[ConversationResponse])
def list_conversations(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return []  # 暂时返回空列表


@router.get("/{upload_id}/conversations/{conv_id}", response_model=ConversationResponse)
def get_conversation(
    upload_id: int,
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raise HTTPException(status_code=404, detail="Conversation not found")


@router.delete("/{upload_id}/conversations/{conv_id}")
def delete_conversation(
    upload_id: int,
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"detail": "Conversation deleted (disabled)"}