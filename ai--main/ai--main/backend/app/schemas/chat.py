from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ChatMessageCreate(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    upload_id: int
    title: str
    created_at: datetime
    messages: list[ChatMessageResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
