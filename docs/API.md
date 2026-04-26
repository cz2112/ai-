# API Documentation

## Base URL

```text
http://127.0.0.1:8000/api
```

## Authentication

All endpoints except the public auth endpoints require:

```text
Authorization: Bearer <access_token>
```

## Health check

```text
GET /api/health
```

Response:

```json
{ "status": "ok" }
```

## Rate-limited endpoints

| Endpoint | Limit |
|---|---|
| `POST /api/auth/register` | 3/minute |
| `POST /api/auth/login` | 5/minute |
| `POST /api/uploads/` | 10/minute |
| `POST /api/uploads/batch` | 5/minute |

## Supported upload file types

```text
pdf, mp3, wav, mp4, mov, pptx, ppt, docx, png, jpg, jpeg
```

## Common response notes

- Upload detail, export, knowledge graph, comments, and chat are readable by:
  - owner
  - admin
  - direct share recipient
  - group member for group-shared files
  - public viewers for `is_shared=true` uploads
- Summary / concept / flashcard editing remains owner-only.

---

## Auth (`/api/auth`)

### `POST /auth/register`

Create a user.

Request JSON:

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "123456"
}
```

Response:

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com"
}
```

### `POST /auth/login`

Login via form-urlencoded.

Form fields:

- `username`
- `password`

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### `GET /auth/me`

Response:

```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "is_admin": false
}
```

### `GET /auth/verify-email`

Query:

- `token`

### `POST /auth/forgot-password`

Request:

```json
{
  "email": "alice@example.com"
}
```

### `POST /auth/reset-password`

Request:

```json
{
  "token": "reset-token",
  "new_password": "new-password"
}
```

---

## Uploads (`/api/uploads`)

### `GET /uploads/`

List current user's uploads.

Query params:

- `search`
- `status`
- `course_id`
- `tag`
- `sort`

Supported `sort` values:

- `-created_at` (default)
- `created_at`
- `filename`
- `-filename`
- `name`
- `name_desc`
- `oldest`
- `size`
- `-file_size`

### `POST /uploads/`

Single upload.

Multipart fields:

- `file`
- `course_id` (optional)

Response shape:

```json
{
  "id": 1,
  "filename": "notes.pdf",
  "file_type": "pdf",
  "file_size": 12345,
  "status": "Pending",
  "is_shared": false,
  "error_message": null,
  "course_id": 1,
  "course_name": "Physics",
  "language": "en",
  "created_at": "2026-04-26T01:00:00Z",
  "updated_at": "2026-04-26T01:00:00Z"
}
```

### `POST /uploads/batch`

Batch upload.

Multipart fields:

- `files`
- `course_id` (optional)

### `GET /uploads/{upload_id}`

Readable by owner / shared user / group member / public viewer / admin.

Response shape:

```json
{
  "id": 1,
  "user_id": 3,
  "filename": "notes.pdf",
  "file_type": "pdf",
  "file_size": 12345,
  "status": "Completed",
  "is_shared": false,
  "error_message": null,
  "transcript": "extracted text",
  "course_id": 1,
  "language": "en",
  "summary": {
    "id": 10,
    "content": "summary text"
  },
  "key_concepts": [],
  "flashcards": [],
  "created_at": "2026-04-26T01:00:00Z",
  "updated_at": "2026-04-26T01:05:00Z"
}
```

### `DELETE /uploads/{upload_id}`

Owner-only.

### `POST /uploads/{upload_id}/retry`

Owner-only. Resets status to `Pending` and requeues processing.

### `GET /uploads/{upload_id}/knowledge-graph`

Readable by owner / shared user / group member / public viewer / admin.

Response:

```json
{
  "nodes": [],
  "edges": []
}
```

### `GET /uploads/{upload_id}/export`

Readable by owner / shared user / group member / public viewer / admin.

Returns Markdown as plain text with `Content-Disposition`.

### `GET /uploads/stats`

Current user's dashboard stats.

### `GET /uploads/quota`

Response:

```json
{
  "uploads_used": 4,
  "uploads_limit": 100,
  "max_file_size_mb": 50,
  "max_audio_minutes": 120,
  "max_pdf_pages": 500
}
```

### `GET /uploads/learning-path/recommend`

Query:

- `upload_id` (optional)

If omitted, it uses the user's most recent completed uploads.

### `PATCH /uploads/summary/{summary_id}`

Owner-only.

Request:

```json
{
  "content": "updated summary"
}
```

### `PATCH /uploads/concepts/{concept_id}`

Owner-only.

Request:

```json
{
  "title": "optional",
  "description": "optional"
}
```

### `PATCH /uploads/flashcards/{flashcard_id}`

Owner-only.

Request:

```json
{
  "question": "optional",
  "answer": "optional",
  "is_known": true
}
```

### `POST /uploads/flashcards/{flashcard_id}/review`

Owner-only SM-2 review.

Request:

```json
{
  "quality": 4
}
```

### `GET /uploads/courses`

List current user's courses.

### `POST /uploads/courses`

Request:

```json
{
  "name": "Physics"
}
```

### `DELETE /uploads/courses/{course_id}`

Deletes the course and unassigns the user's uploads from it.

### `GET /uploads/tags/list`

List current user's tags.

### `POST /uploads/tags`

Request:

```json
{
  "name": "important"
}
```

### `DELETE /uploads/tags/{tag_id}`

Delete one tag.

---

## Chat (`/api/chat`)

These endpoints require upload read access and a transcript.

Conversations are per-user even when multiple users can read the same upload.

### `POST /chat/{upload_id}`

Request:

```json
{
  "message": "Explain the main point",
  "conversation_id": null
}
```

Response:

```json
{
  "id": 12,
  "role": "assistant",
  "content": "answer text",
  "created_at": "2026-04-26T01:10:00Z"
}
```

### `GET /chat/{upload_id}/conversations`

List current user's conversations for this upload.

### `GET /chat/{upload_id}/conversations/{conv_id}`

Returns one conversation and all messages.

### `DELETE /chat/{upload_id}/conversations/{conv_id}`

Deletes the current user's conversation.

---

## Share (`/api/share`)

### Sharing semantics

- `is_shared=false` does not block direct shares or group shares.
- `Private + group share` means only group members can access the file.
- `is_shared=true` makes the upload globally visible in shared materials.

### `POST /share/`

Create or update a share.

Request:

```json
{
  "upload_id": 1,
  "shared_with": 2,
  "shared_with_username": null,
  "group_id": null,
  "message": "optional note",
  "permission": "read"
}
```

Notes:

- set `shared_with`
- or set `shared_with_username`
- or set `group_id`

### `GET /share/mine`

Query:

- `upload_id` (optional)

Lists shares created by the current user.

### `PATCH /share/uploads/{upload_id}/visibility`

Owner-only public/private toggle.

Request:

```json
{
  "is_shared": true
}
```

Response:

```json
{
  "upload_id": 1,
  "is_shared": true
}
```

### `GET /share/shared-with-me`

Returns:

- direct shares to the current user
- explicit public share records
- group shares for groups the user belongs to
- uploads whose `is_shared=true`

### `DELETE /share/{share_id}`

Only the share creator can remove it.

### `POST /share/{upload_id}/comments`

Requires upload read access.

Request:

```json
{
  "content": "Useful notes"
}
```

### `GET /share/{upload_id}/comments`

Requires upload read access.

### `DELETE /share/comments/{comment_id}`

Only the comment author can delete it.

---

## Study groups (`/api/share/groups...`)

### `POST /share/groups`

Request:

```json
{
  "name": "Physics Group",
  "description": "optional",
  "join_mode": "open"
}
```

`join_mode`:

- `open`
- `approval`

### `GET /share/groups`

Groups current user belongs to.

### `GET /share/groups/all`

All discoverable groups.

### `PATCH /share/groups/{group_id}`

Owner-only.

Request:

```json
{
  "join_mode": "approval"
}
```

### `GET /share/groups/{group_id}/members`

Member-only.

### `POST /share/groups/{group_id}/join`

- joins immediately for `open`
- creates a join request for `approval`

### `POST /share/groups/{group_id}/leave`

Non-owner member leaves the group.

### `DELETE /share/groups/{group_id}`

Owner-only delete.

### `GET /share/groups/{group_id}/join-requests`

Owner-only list of pending join requests.

### `POST /share/groups/{group_id}/join-requests/{request_id}/approve`

Owner-only.

### `POST /share/groups/{group_id}/join-requests/{request_id}/reject`

Owner-only.

### `POST /share/groups/{group_id}/invite`

Member-only invite by username or email.

Request:

```json
{
  "username_or_email": "alice"
}
```

### `GET /share/groups/invites/mine`

Current user's pending invites.

### `POST /share/groups/invites/{invite_id}/accept`

### `POST /share/groups/invites/{invite_id}/decline`

### `POST /share/groups/{group_id}/messages`

Member-only.

Request:

```json
{
  "content": "hello team"
}
```

### `GET /share/groups/{group_id}/messages`

Member-only. Returns up to 200 messages.

### `POST /share/groups/{group_id}/files`

Share one of the current user's uploads into the group.

Request:

```json
{
  "upload_id": 10
}
```

### `GET /share/groups/{group_id}/files`

Member-only. Lists group-shared files.

### `DELETE /share/groups/{group_id}/files/{share_id}`

Allowed for:

- the original sharer
- the group owner

---

## Admin (`/api/admin`)

All admin endpoints require `is_admin=true`.

There is no automatic default admin bootstrap in the application.

### `GET /admin/users`

List users with:

- `id`
- `username`
- `email`
- `is_admin`
- `is_active`
- `created_at`
- `upload_count`

### `PATCH /admin/users/{user_id}/toggle`

Toggle active status.

Admins cannot disable themselves.

### `DELETE /admin/users/{user_id}`

Deletes the user and their upload files.

Admins cannot delete themselves.

### `GET /admin/uploads`

List uploads across all users.

Query:

- `search`
- `status`
- `user_id`

Response items include:

- `id`
- `filename`
- `file_type`
- `file_size`
- `status`
- `is_shared`
- `created_at`
- `username`

### `PATCH /admin/uploads/{upload_id}/toggle-share`

Toggle an upload's public flag as admin.

### `DELETE /admin/uploads/{upload_id}`

Delete any upload.

### `GET /admin/stats`

Response:

```json
{
  "total_users": 10,
  "total_uploads": 25,
  "total_storage_mb": 12.4,
  "uploads_by_status": {
    "Completed": 20,
    "Pending": 2,
    "Processing": 1,
    "Failed": 2
  },
  "recent_users": []
}
```

### `GET /admin/settings`

### `PATCH /admin/settings`

Request fields are all optional:

```json
{
  "max_uploads_per_user": 100,
  "max_upload_size_mb": 50,
  "max_audio_minutes": 120,
  "max_pdf_pages": 500
}
```

Response shape:

```json
{
  "max_uploads_per_user": 100,
  "max_upload_size_mb": 50,
  "max_audio_minutes": 120,
  "max_pdf_pages": 500
}
```

---

## Error patterns

Common examples:

- `401 Could not validate credentials`
- `403 Admin access required`
- `404 Upload not found`
- `404 Upload not found or not yours`
- `404 Upload not found or not shared with you`
- `400 Comment cannot be empty`
- `400 Message cannot be empty`
- `400 Quality must be between 0 and 5`
