from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import false, or_
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.upload import Upload
from app.models.share import SharedUpload, Comment, StudyGroup, GroupMember, JoinRequest, GroupInvite, GroupMessage
from app.schemas.share import (
    ShareCreate, ShareResponse, CommentCreate, CommentResponse,
    StudyGroupCreate, StudyGroupResponse, StudyGroupUpdate, GroupMemberResponse,
    JoinRequestResponse, GroupInviteCreate, GroupInviteResponse,
    GroupMessageCreate, GroupMessageResponse,
    GroupFileShareCreate, GroupFileResponse,
    ShareVisibilityUpdate, ShareVisibilityResponse,
)
from app.services.upload_access import get_user_group_ids, user_can_access_upload

router = APIRouter(prefix="/api/share", tags=["share"])


def _serialize_share(db: Session, share: SharedUpload) -> ShareResponse:
    upload = db.query(Upload).filter(Upload.id == share.upload_id).first()
    owner = db.query(User).filter(User.id == share.shared_by).first()
    group_name = ""
    if share.group_id:
        group = db.query(StudyGroup).filter(StudyGroup.id == share.group_id).first()
        group_name = group.name if group else ""
    return ShareResponse(
        id=share.id,
        upload_id=share.upload_id,
        shared_by=share.shared_by,
        shared_with=share.shared_with,
        group_id=share.group_id,
        message=share.message,
        permission=share.permission or "read",
        created_at=share.created_at,
        filename=upload.filename if upload else "",
        owner_name=owner.username if owner else "",
        group_name=group_name,
    )


# ── Sharing ──────────────────────────────────────────────

@router.post("/", response_model=ShareResponse)
def share_upload(data: ShareCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == data.upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found or not yours")

    shared_with = data.shared_with
    if shared_with is None and data.shared_with_username:
        target_user = db.query(User).filter(
            or_(User.username == data.shared_with_username, User.email == data.shared_with_username)
        ).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        shared_with = target_user.id
    if shared_with == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot share with yourself")
    if data.group_id is not None:
        membership = db.query(GroupMember).filter(
            GroupMember.group_id == data.group_id,
            GroupMember.user_id == current_user.id,
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="You must be a member of the group to share files there")

    existing = db.query(SharedUpload).filter(
        SharedUpload.upload_id == data.upload_id,
        SharedUpload.shared_with == shared_with,
        SharedUpload.group_id == data.group_id,
    ).first()
    if existing:
        existing.message = data.message
        existing.permission = (data.permission or existing.permission or "read").strip()
        db.commit()
        db.refresh(existing)
        return _serialize_share(db, existing)

    share = SharedUpload(
        upload_id=data.upload_id,
        shared_by=current_user.id,
        shared_with=shared_with,
        group_id=data.group_id,
        message=data.message,
        permission=(data.permission or "read").strip() or "read",
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return _serialize_share(db, share)


@router.get("/mine", response_model=list[ShareResponse])
def list_my_shares(upload_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(SharedUpload).filter(SharedUpload.shared_by == current_user.id)
    if upload_id is not None:
        query = query.filter(SharedUpload.upload_id == upload_id)
    shares = query.order_by(SharedUpload.created_at.desc(), SharedUpload.id.desc()).all()
    return [_serialize_share(db, share) for share in shares]


@router.patch("/uploads/{upload_id}/visibility", response_model=ShareVisibilityResponse)
def update_upload_visibility(
    upload_id: int,
    data: ShareVisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found or not yours")
    upload.is_shared = data.is_shared
    db.commit()
    db.refresh(upload)
    return ShareVisibilityResponse(upload_id=upload.id, is_shared=bool(upload.is_shared))


@router.get("/shared-with-me", response_model=list[ShareResponse])
def get_shared_with_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group_ids = get_user_group_ids(db, current_user.id)

    # 1) Explicit direct shares, explicit public shares, and shares posted into my groups.
    shares = db.query(SharedUpload).filter(
        (SharedUpload.shared_with == current_user.id)
        | ((SharedUpload.shared_with == None) & (SharedUpload.group_id == None))
        | (SharedUpload.group_id.in_(group_ids) if group_ids else false())
    ).order_by(SharedUpload.created_at.desc()).all()
    result = []
    seen_upload_ids = set()
    for s in shares:
        seen_upload_ids.add(s.upload_id)
        result.append(_serialize_share(db, s))
    # 2) Admin-toggled public files (is_shared=True), exclude own files and duplicates
    public_uploads = db.query(Upload).filter(
        Upload.is_shared == True, Upload.user_id != current_user.id
    ).order_by(Upload.created_at.desc()).all()
    for u in public_uploads:
        if u.id in seen_upload_ids:
            continue
        owner = db.query(User).filter(User.id == u.user_id).first()
        result.append(ShareResponse(
            id=0, upload_id=u.id, shared_by=u.user_id,
            shared_with=None, group_id=None,
            message="Publicly shared", permission="read", created_at=u.created_at,
            filename=u.filename,
            owner_name=owner.username if owner else "", group_name="",
        ))
    return result


@router.delete("/{share_id}")
def delete_share(share_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    share = db.query(SharedUpload).filter(SharedUpload.id == share_id, SharedUpload.shared_by == current_user.id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    db.delete(share)
    db.commit()
    return {"detail": "Share removed"}


# ── Comments ─────────────────────────────────────────────

@router.post("/{upload_id}/comments", response_model=CommentResponse)
def add_comment(upload_id: int, data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not user_can_access_upload(db, current_user.id, upload_id):
        raise HTTPException(status_code=404, detail="Upload not found or not shared with you")
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    comment = Comment(upload_id=upload_id, user_id=current_user.id, content=data.content.strip())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentResponse(
        id=comment.id, upload_id=comment.upload_id, user_id=comment.user_id,
        content=comment.content, created_at=comment.created_at,
        username=current_user.username,
    )


@router.get("/{upload_id}/comments", response_model=list[CommentResponse])
def list_comments(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not user_can_access_upload(db, current_user.id, upload_id):
        raise HTTPException(status_code=404, detail="Upload not found or not shared with you")
    comments = db.query(Comment).filter(Comment.upload_id == upload_id).order_by(Comment.created_at.asc()).all()
    result = []
    for c in comments:
        user = db.query(User).filter(User.id == c.user_id).first()
        result.append(CommentResponse(
            id=c.id, upload_id=c.upload_id, user_id=c.user_id,
            content=c.content, created_at=c.created_at,
            username=user.username if user else "",
        ))
    return result


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.user_id == current_user.id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db.delete(comment)
    db.commit()
    return {"detail": "Comment deleted"}


# ── Study Groups ─────────────────────────────────────────

@router.post("/groups", response_model=StudyGroupResponse)
def create_group(data: StudyGroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = StudyGroup(name=data.name, description=data.description, owner_id=current_user.id, join_mode=data.join_mode)
    db.add(group)
    db.commit()
    db.refresh(group)
    # Add owner as member
    member = GroupMember(group_id=group.id, user_id=current_user.id, role="owner")
    db.add(member)
    db.commit()
    return StudyGroupResponse(
        id=group.id, name=group.name, description=group.description,
        owner_id=group.owner_id, created_at=group.created_at,
        member_count=1, owner_name=current_user.username,
        join_mode=group.join_mode,
    )


@router.get("/groups", response_model=list[StudyGroupResponse])
def list_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memberships = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    group_ids = [m.group_id for m in memberships]
    groups = db.query(StudyGroup).filter(StudyGroup.id.in_(group_ids)).all() if group_ids else []
    result = []
    for g in groups:
        count = db.query(GroupMember).filter(GroupMember.group_id == g.id).count()
        owner = db.query(User).filter(User.id == g.owner_id).first()
        result.append(StudyGroupResponse(
            id=g.id, name=g.name, description=g.description,
            owner_id=g.owner_id, created_at=g.created_at,
            member_count=count, owner_name=owner.username if owner else "",
            join_mode=g.join_mode or "open",
        ))
    return result


@router.get("/groups/all", response_model=list[StudyGroupResponse])
def list_all_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    groups = db.query(StudyGroup).order_by(StudyGroup.created_at.desc()).all()
    result = []
    for g in groups:
        count = db.query(GroupMember).filter(GroupMember.group_id == g.id).count()
        owner = db.query(User).filter(User.id == g.owner_id).first()
        result.append(StudyGroupResponse(
            id=g.id, name=g.name, description=g.description,
            owner_id=g.owner_id, created_at=g.created_at,
            member_count=count, owner_name=owner.username if owner else "",
            join_mode=g.join_mode or "open",
        ))
    return result


@router.patch("/groups/{group_id}", response_model=StudyGroupResponse)
def update_group(group_id: int, data: StudyGroupUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id, StudyGroup.owner_id == current_user.id).first()
    if not group:
        raise HTTPException(status_code=403, detail="Only the group owner can update settings")
    if data.join_mode is not None:
        if data.join_mode not in ("open", "approval"):
            raise HTTPException(status_code=400, detail="join_mode must be 'open' or 'approval'")
        group.join_mode = data.join_mode
    db.commit()
    db.refresh(group)
    count = db.query(GroupMember).filter(GroupMember.group_id == group.id).count()
    return StudyGroupResponse(
        id=group.id, name=group.name, description=group.description,
        owner_id=group.owner_id, created_at=group.created_at,
        member_count=count, owner_name=current_user.username,
        join_mode=group.join_mode or "open",
    )


@router.get("/groups/{group_id}/members", response_model=list[GroupMemberResponse])
def list_group_members(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify user is a member
    membership = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append(GroupMemberResponse(
            id=m.id, user_id=m.user_id, role=m.role,
            joined_at=m.joined_at, username=user.username if user else "",
        ))
    return result


@router.post("/groups/{group_id}/join")
def join_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    existing = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")
    if group.join_mode == "approval":
        existing_req = db.query(JoinRequest).filter(
            JoinRequest.group_id == group_id, JoinRequest.user_id == current_user.id, JoinRequest.status == "pending"
        ).first()
        if existing_req:
            raise HTTPException(status_code=400, detail="Join request already pending")
        req = JoinRequest(group_id=group_id, user_id=current_user.id, status="pending")
        db.add(req)
        db.commit()
        return {"detail": "Join request sent"}
    member = GroupMember(group_id=group_id, user_id=current_user.id, role="member")
    db.add(member)
    db.commit()
    return {"detail": "Joined group"}


@router.post("/groups/{group_id}/leave")
def leave_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Not a member")
    if member.role == "owner":
        raise HTTPException(status_code=400, detail="Owner cannot leave. Delete the group instead.")
    db.delete(member)
    db.commit()
    return {"detail": "Left group"}


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id, StudyGroup.owner_id == current_user.id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found or not owner")
    db.query(SharedUpload).filter(SharedUpload.group_id == group_id).delete()
    db.query(JoinRequest).filter(JoinRequest.group_id == group_id).delete()
    db.query(GroupInvite).filter(GroupInvite.group_id == group_id).delete()
    db.query(GroupMessage).filter(GroupMessage.group_id == group_id).delete()
    db.delete(group)
    db.commit()
    return {"detail": "Group deleted"}


# ── Join Requests ───────────────────────────────────────

@router.get("/groups/{group_id}/join-requests", response_model=list[JoinRequestResponse])
def list_join_requests(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id, StudyGroup.owner_id == current_user.id).first()
    if not group:
        raise HTTPException(status_code=403, detail="Only the group owner can view join requests")
    requests = db.query(JoinRequest).filter(JoinRequest.group_id == group_id, JoinRequest.status == "pending").all()
    result = []
    for r in requests:
        user = db.query(User).filter(User.id == r.user_id).first()
        result.append(JoinRequestResponse(
            id=r.id, group_id=r.group_id, user_id=r.user_id,
            status=r.status, created_at=r.created_at,
            username=user.username if user else "",
        ))
    return result


@router.post("/groups/{group_id}/join-requests/{request_id}/approve")
def approve_join_request(group_id: int, request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id, StudyGroup.owner_id == current_user.id).first()
    if not group:
        raise HTTPException(status_code=403, detail="Only the group owner can approve requests")
    req = db.query(JoinRequest).filter(JoinRequest.id == request_id, JoinRequest.group_id == group_id, JoinRequest.status == "pending").first()
    if not req:
        raise HTTPException(status_code=404, detail="Join request not found")
    req.status = "approved"
    member = GroupMember(group_id=group_id, user_id=req.user_id, role="member")
    db.add(member)
    db.commit()
    return {"detail": "Request approved"}


@router.post("/groups/{group_id}/join-requests/{request_id}/reject")
def reject_join_request(group_id: int, request_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id, StudyGroup.owner_id == current_user.id).first()
    if not group:
        raise HTTPException(status_code=403, detail="Only the group owner can reject requests")
    req = db.query(JoinRequest).filter(JoinRequest.id == request_id, JoinRequest.group_id == group_id, JoinRequest.status == "pending").first()
    if not req:
        raise HTTPException(status_code=404, detail="Join request not found")
    req.status = "rejected"
    db.commit()
    return {"detail": "Request rejected"}


# ── Invites ─────────────────────────────────────────────

@router.post("/groups/{group_id}/invite", response_model=GroupInviteResponse)
def invite_to_group(group_id: int, data: GroupInviteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You must be a member to invite others")
    invitee = db.query(User).filter(
        or_(User.username == data.username_or_email, User.email == data.username_or_email)
    ).first()
    if not invitee:
        raise HTTPException(status_code=404, detail="User not found")
    if invitee.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot invite yourself")
    existing_member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == invitee.id).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member")
    existing_invite = db.query(GroupInvite).filter(
        GroupInvite.group_id == group_id, GroupInvite.invitee_id == invitee.id, GroupInvite.status == "pending"
    ).first()
    if existing_invite:
        raise HTTPException(status_code=400, detail="Invite already pending")
    group = db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
    invite = GroupInvite(group_id=group_id, inviter_id=current_user.id, invitee_id=invitee.id)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return GroupInviteResponse(
        id=invite.id, group_id=invite.group_id, inviter_id=invite.inviter_id,
        invitee_id=invite.invitee_id, status=invite.status, created_at=invite.created_at,
        invitee_name=invitee.username, inviter_name=current_user.username,
        group_name=group.name if group else "",
    )


@router.get("/groups/invites/mine", response_model=list[GroupInviteResponse])
def list_my_invites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invites = db.query(GroupInvite).filter(GroupInvite.invitee_id == current_user.id, GroupInvite.status == "pending").all()
    result = []
    for inv in invites:
        group = db.query(StudyGroup).filter(StudyGroup.id == inv.group_id).first()
        inviter = db.query(User).filter(User.id == inv.inviter_id).first()
        result.append(GroupInviteResponse(
            id=inv.id, group_id=inv.group_id, inviter_id=inv.inviter_id,
            invitee_id=inv.invitee_id, status=inv.status, created_at=inv.created_at,
            invitee_name=current_user.username, inviter_name=inviter.username if inviter else "",
            group_name=group.name if group else "",
        ))
    return result


@router.post("/groups/invites/{invite_id}/accept")
def accept_invite(invite_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite = db.query(GroupInvite).filter(GroupInvite.id == invite_id, GroupInvite.invitee_id == current_user.id, GroupInvite.status == "pending").first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    invite.status = "accepted"
    existing = db.query(GroupMember).filter(GroupMember.group_id == invite.group_id, GroupMember.user_id == current_user.id).first()
    if not existing:
        member = GroupMember(group_id=invite.group_id, user_id=current_user.id, role="member")
        db.add(member)
    db.commit()
    return {"detail": "Invite accepted"}


@router.post("/groups/invites/{invite_id}/decline")
def decline_invite(invite_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite = db.query(GroupInvite).filter(GroupInvite.id == invite_id, GroupInvite.invitee_id == current_user.id, GroupInvite.status == "pending").first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    invite.status = "declined"
    db.commit()
    return {"detail": "Invite declined"}


# ── Group Chat ──────────────────────────────────────────

@router.post("/groups/{group_id}/messages", response_model=GroupMessageResponse)
def send_group_message(group_id: int, data: GroupMessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You must be a member to send messages")
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    msg = GroupMessage(group_id=group_id, user_id=current_user.id, content=data.content.strip())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return GroupMessageResponse(
        id=msg.id, group_id=msg.group_id, user_id=msg.user_id,
        content=msg.content, created_at=msg.created_at,
        username=current_user.username,
    )


@router.get("/groups/{group_id}/messages", response_model=list[GroupMessageResponse])
def list_group_messages(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You must be a member to view messages")
    messages = db.query(GroupMessage).filter(GroupMessage.group_id == group_id).order_by(GroupMessage.created_at.asc()).limit(200).all()
    result = []
    for m in messages:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append(GroupMessageResponse(
            id=m.id, group_id=m.group_id, user_id=m.user_id,
            content=m.content, created_at=m.created_at,
            username=user.username if user else "",
        ))
    return result


# ── Group Files ────────────────────────────────────────

@router.post("/groups/{group_id}/files", response_model=GroupFileResponse)
def share_file_to_group(group_id: int, data: GroupFileShareCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You must be a member to share files")
    upload = db.query(Upload).filter(Upload.id == data.upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found or not yours")
    existing = db.query(SharedUpload).filter(
        SharedUpload.upload_id == data.upload_id, SharedUpload.group_id == group_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="File already shared to this group")
    share = SharedUpload(upload_id=data.upload_id, shared_by=current_user.id, group_id=group_id, permission="read")
    db.add(share)
    db.commit()
    db.refresh(share)
    return GroupFileResponse(
        id=share.id, upload_id=upload.id, filename=upload.filename,
        file_type=upload.file_type, shared_by=current_user.id,
        owner_name=current_user.username, permission=share.permission or "read", created_at=share.created_at,
    )


@router.get("/groups/{group_id}/files", response_model=list[GroupFileResponse])
def list_group_files(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You must be a member to view files")
    shares = db.query(SharedUpload).filter(SharedUpload.group_id == group_id).order_by(SharedUpload.created_at.desc()).all()
    result = []
    for s in shares:
        upload = db.query(Upload).filter(Upload.id == s.upload_id).first()
        owner = db.query(User).filter(User.id == s.shared_by).first()
        if upload:
            result.append(GroupFileResponse(
                id=s.id, upload_id=upload.id, filename=upload.filename,
                file_type=upload.file_type, shared_by=s.shared_by,
                owner_name=owner.username if owner else "", permission=s.permission or "read", created_at=s.created_at,
            ))
    return result


@router.delete("/groups/{group_id}/files/{share_id}")
def remove_group_file(group_id: int, share_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    share = db.query(SharedUpload).filter(SharedUpload.id == share_id, SharedUpload.group_id == group_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Shared file not found")
    if share.shared_by != current_user.id:
        group = db.query(StudyGroup).filter(StudyGroup.id == group_id, StudyGroup.owner_id == current_user.id).first()
        if not group:
            raise HTTPException(status_code=403, detail="Only the file sharer or group owner can remove")
    db.delete(share)
    db.commit()
    return {"detail": "File removed from group"}
