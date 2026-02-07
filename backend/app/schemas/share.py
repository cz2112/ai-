from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ShareCreate(BaseModel):
    upload_id: int
    shared_with: Optional[int] = None  # user_id, null = public
    group_id: Optional[int] = None
    message: Optional[str] = None


class ShareResponse(BaseModel):
    id: int
    upload_id: int
    shared_by: int
    shared_with: Optional[int] = None
    group_id: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime
    filename: str = ""
    owner_name: str = ""

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    upload_id: int
    user_id: int
    content: str
    created_at: datetime
    username: str = ""

    class Config:
        from_attributes = True


class StudyGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    join_mode: str = "open"


class StudyGroupUpdate(BaseModel):
    join_mode: Optional[str] = None


class StudyGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: datetime
    member_count: int = 0
    owner_name: str = ""
    join_mode: str = "open"

    class Config:
        from_attributes = True


class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    role: str
    joined_at: datetime
    username: str = ""

    class Config:
        from_attributes = True


class JoinRequestResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    status: str
    created_at: datetime
    username: str = ""

    class Config:
        from_attributes = True


class GroupInviteCreate(BaseModel):
    username_or_email: str


class GroupInviteResponse(BaseModel):
    id: int
    group_id: int
    inviter_id: int
    invitee_id: int
    status: str
    created_at: datetime
    invitee_name: str = ""
    inviter_name: str = ""
    group_name: str = ""

    class Config:
        from_attributes = True


class GroupMessageCreate(BaseModel):
    content: str


class GroupMessageResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    content: str
    created_at: datetime
    username: str = ""

    class Config:
        from_attributes = True


class GroupFileShareCreate(BaseModel):
    upload_id: int


class GroupFileResponse(BaseModel):
    id: int
    upload_id: int
    filename: str = ""
    file_type: str = ""
    shared_by: int
    owner_name: str = ""
    created_at: datetime

    class Config:
        from_attributes = True
