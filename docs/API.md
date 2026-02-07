# API Documentation

## Base URL

```
http://localhost:8000/api
```

## Authentication

All endpoints except `POST /api/auth/register` and `POST /api/auth/login` require a Bearer token in the `Authorization` header.

```
Authorization: Bearer <access_token>
```

Tokens are obtained via the login endpoint and are JWT-based.

## Rate Limiting

Several endpoints enforce rate limits:

| Endpoint | Limit |
|---|---|
| `POST /api/auth/register` | 3 requests/minute |
| `POST /api/auth/login` | 5 requests/minute |
| `POST /api/uploads/` | 10 requests/minute |
| `POST /api/uploads/batch` | 5 requests/minute |

## Allowed File Types

Uploads accept the following extensions: `pdf`, `mp3`, `wav`, `pptx`, `ppt`, `docx`, `png`, `jpg`, `jpeg`.

## Common Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Meaning |
|---|---|
| 400 | Bad Request -- Invalid input or business rule violation |
| 401 | Unauthorized -- Missing or invalid token |
| 403 | Forbidden -- Insufficient permissions |
| 404 | Not Found -- Resource does not exist |
| 429 | Too Many Requests -- Rate limit exceeded |

---

## Endpoints

### Auth (`/api/auth`)

---

#### POST /api/auth/register

Register a new user account.

**Auth required:** No

**Rate limit:** 3 requests/minute

**Request Body (JSON):**

```json
{
  "username": "string (required)",
  "email": "string (required)",
  "password": "string (required, min 6 characters)"
}
```

**Response (200):**

```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 400 | `"Username already exists"` |
| 400 | `"Email already exists"` |
| 422 | Validation error (password too short, invalid email, etc.) |

---

#### POST /api/auth/login

Authenticate and receive an access token. Uses OAuth2 password form encoding.

**Auth required:** No

**Rate limit:** 5 requests/minute

**Request Body (application/x-www-form-urlencoded):**

| Field | Type | Description |
|---|---|---|
| `username` | string | The user's username |
| `password` | string | The user's password |

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 401 | `"Incorrect username or password"` |

---

#### GET /api/auth/me

Get the currently authenticated user's profile.

**Auth required:** Yes (Bearer token)

**Response (200):**

```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "is_admin": false
}
```

---

### Uploads (`/api/uploads`)

---

#### GET /api/uploads/

List all uploads for the current user. Supports filtering and sorting.

**Auth required:** Yes

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `search` | string | null | Filter by filename (case-insensitive partial match) |
| `status` | string | null | Filter by status (`Pending`, `Processing`, `Completed`, `Failed`) |
| `course_id` | integer | null | Filter by course ID |
| `tag` | string | null | Filter by tag name |
| `sort` | string | `"newest"` | Sort order: `newest`, `oldest`, `name`, `size` |

**Response (200):**

```json
[
  {
    "id": 1,
    "filename": "lecture-notes.pdf",
    "file_type": "pdf",
    "file_size": 204800,
    "status": "Completed",
    "error_message": null,
    "course_id": 1,
    "language": "en",
    "created_at": "2026-01-15T10:30:00",
    "updated_at": "2026-01-15T10:35:00"
  }
]
```

---

#### POST /api/uploads/

Upload a single file. The file is processed asynchronously after upload.

**Auth required:** Yes

**Rate limit:** 10 requests/minute

**Request Body (multipart/form-data):**

| Field | Type | Description |
|---|---|---|
| `file` | file (required) | The file to upload |
| `course_id` | integer (optional) | Associate with a course |

**Response (200):**

```json
{
  "id": 1,
  "filename": "lecture-notes.pdf",
  "file_type": "pdf",
  "file_size": 204800,
  "status": "Pending",
  "error_message": null,
  "course_id": 1,
  "language": "en",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 400 | `"Upload quota reached (N)"` |
| 400 | `"Unsupported file type: .xyz"` |
| 400 | `"File too large (max NMB)"` |
| 400 | `"File content does not match its extension"` |

---

#### POST /api/uploads/batch

Upload multiple files at once. Files that exceed size limits or have unsupported types are silently skipped.

**Auth required:** Yes

**Rate limit:** 5 requests/minute

**Request Body (multipart/form-data):**

| Field | Type | Description |
|---|---|---|
| `files` | file[] (required) | Multiple files to upload |
| `course_id` | integer (optional) | Associate all uploads with a course |

**Response (200):** Array of `UploadResponse` objects (same schema as single upload).

**Error Responses:**

| Status | Detail |
|---|---|
| 400 | `"Upload quota would be exceeded"` |

---

#### GET /api/uploads/stats

Get statistics about the current user's uploads and study activity.

**Auth required:** Yes

**Response (200):**

```json
{
  "total_uploads": 12,
  "completed_uploads": 10,
  "total_flashcards": 150,
  "known_flashcards": 85,
  "total_concepts": 45,
  "uploads_by_date": [
    { "date": "2026-01-15", "count": 3 }
  ],
  "uploads_by_status": {
    "Completed": 10,
    "Pending": 1,
    "Failed": 1
  },
  "study_activity_by_date": [
    { "date": "2026-01-15", "count": 5 }
  ]
}
```

---

#### GET /api/uploads/quota

Get the current user's upload quota and limits.

**Auth required:** Yes

**Response (200):**

```json
{
  "uploads_used": 5,
  "uploads_limit": 50,
  "max_file_size_mb": 25,
  "max_audio_minutes": 60,
  "max_pdf_pages": 200
}
```

---

#### GET /api/uploads/{upload_id}

Get detailed information about a specific upload, including its summary, key concepts, and flashcards.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |

**Response (200):**

```json
{
  "id": 1,
  "filename": "lecture-notes.pdf",
  "file_type": "pdf",
  "file_size": 204800,
  "status": "Completed",
  "error_message": null,
  "transcript": "Full extracted text content...",
  "course_id": 1,
  "language": "en",
  "summary": {
    "id": 1,
    "content": "This lecture covers..."
  },
  "key_concepts": [
    {
      "id": 1,
      "title": "Machine Learning",
      "description": "A subset of AI that...",
      "citation": "Page 5, paragraph 2"
    }
  ],
  "flashcards": [
    {
      "id": 1,
      "question": "What is supervised learning?",
      "answer": "A type of ML where...",
      "is_known": false
    }
  ],
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:35:00"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |

---

#### PATCH /api/uploads/{upload_id}

Update an upload's course assignment.

**Auth required:** Yes

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `course_id` | integer | The new course ID (or null to unassign) |

**Response (200):** `UploadResponse` object.

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |

---

#### POST /api/uploads/{upload_id}/retry

Retry processing a failed upload.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |

**Response (200):** `UploadResponse` object with status reset to `"Pending"`.

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |
| 400 | `"Only failed uploads can be retried"` |

---

#### DELETE /api/uploads/{upload_id}

Delete an upload and its associated file from disk.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |

**Response (200):**

```json
{
  "detail": "Deleted"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |

---

#### GET /api/uploads/{upload_id}/export

Export an upload's study materials (summary, key concepts, flashcards) as a Markdown file download.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `fmt` | string | `"markdown"` | Export format |

**Response (200):** Plain text Markdown file with `Content-Disposition: attachment` header.

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |
| 400 | `"Upload not completed yet"` |

---

#### PATCH /api/uploads/summary/{summary_id}

Edit an AI-generated summary.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `summary_id` | integer | The summary ID |

**Request Body (JSON):**

```json
{
  "content": "Updated summary text..."
}
```

**Response (200):**

```json
{
  "id": 1,
  "content": "Updated summary text..."
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Summary not found"` |

---

#### PATCH /api/uploads/flashcards/{flashcard_id}

Edit an AI-generated flashcard.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `flashcard_id` | integer | The flashcard ID |

**Request Body (JSON):**

```json
{
  "question": "Updated question? (optional)",
  "answer": "Updated answer (optional)",
  "is_known": true
}
```

All fields are optional; only provided fields are updated.

**Response (200):**

```json
{
  "id": 1,
  "question": "What is ML?",
  "answer": "Machine Learning is...",
  "is_known": true
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Flashcard not found"` |

---

#### PATCH /api/uploads/concepts/{concept_id}

Edit an AI-generated key concept.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `concept_id` | integer | The concept ID |

**Request Body (JSON):**

```json
{
  "title": "Updated title (optional)",
  "description": "Updated description (optional)"
}
```

All fields are optional; only provided fields are updated.

**Response (200):**

```json
{
  "id": 1,
  "title": "Machine Learning",
  "description": "Updated description...",
  "citation": "Page 5"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Concept not found"` |

---

#### POST /api/uploads/flashcards/{flashcard_id}/review

Submit a review for a flashcard using the SM-2 spaced repetition algorithm.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `flashcard_id` | integer | The flashcard ID |

**Request Body (JSON):**

```json
{
  "quality": 4
}
```

The `quality` field is an integer from 0 to 5:

| Value | Meaning |
|---|---|
| 0 | Complete blackout |
| 1 | Incorrect, but remembered upon seeing answer |
| 2 | Incorrect, but answer seemed easy to recall |
| 3 | Correct with serious difficulty |
| 4 | Correct after hesitation |
| 5 | Perfect response |

**Response (200):**

```json
{
  "flashcard_id": 1,
  "next_review": "2026-01-18T10:30:00",
  "easiness": 2.6,
  "interval_days": 3,
  "repetitions": 2
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Flashcard not found"` |
| 400 | `"Quality must be 0-5"` |

---

#### GET /api/uploads/flashcards/due

Get all flashcards that are due for review based on the SM-2 schedule.

**Auth required:** Yes

**Response (200):**

```json
[
  {
    "id": 1,
    "question": "What is supervised learning?",
    "answer": "A type of ML where...",
    "upload_id": 1,
    "filename": "lecture-notes.pdf",
    "next_review": "2026-01-15T10:30:00",
    "easiness": 2.5,
    "interval_days": 1,
    "repetitions": 1
  }
]
```

Flashcards that have never been reviewed are also included (with `next_review: null`).

---

#### GET /api/uploads/{upload_id}/knowledge-graph

Generate a knowledge graph from the upload's transcript using AI.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |

**Response (200):** JSON object representing the knowledge graph (nodes and edges). Structure depends on AI output.

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |
| 400 | `"No transcript available"` |

---

#### GET /api/uploads/learning-path/recommend

Generate a personalized learning path recommendation based on all completed uploads and known flashcards.

**Auth required:** Yes

**Response (200):** JSON array of learning path recommendations. Structure depends on AI output. Returns an empty array if no completed uploads exist.

---

#### POST /api/uploads/study-sessions

Record a study session.

**Auth required:** Yes

**Request Body (JSON):**

```json
{
  "upload_id": 1,
  "activity_type": "flashcard_review",
  "cards_reviewed": 20,
  "cards_known": 15,
  "duration_seconds": 600
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `upload_id` | integer | No | Associated upload ID |
| `activity_type` | string | Yes | Type of activity (e.g., `"flashcard_review"`, `"reading"`) |
| `cards_reviewed` | integer | No | Number of cards reviewed (default: 0) |
| `cards_known` | integer | No | Number of cards marked known (default: 0) |
| `duration_seconds` | integer | No | Session duration in seconds (default: 0) |

**Response (200):**

```json
{
  "id": 1,
  "upload_id": 1,
  "activity_type": "flashcard_review",
  "cards_reviewed": 20,
  "cards_known": 15,
  "duration_seconds": 600,
  "created_at": "2026-01-15T10:30:00"
}
```

---

#### GET /api/uploads/study-sessions/progress

Get study progress aggregated by date.

**Auth required:** Yes

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `days` | integer | 30 | Number of most recent days to return |

**Response (200):**

```json
[
  {
    "date": "2026-01-15",
    "cards_reviewed": 40,
    "cards_known": 30,
    "duration_minutes": 25,
    "sessions": 3
  }
]
```

---

#### GET /api/uploads/courses

List all courses for the current user.

**Auth required:** Yes

**Response (200):**

```json
[
  {
    "id": 1,
    "name": "Introduction to AI",
    "upload_count": 5,
    "created_at": "2026-01-10T08:00:00"
  }
]
```

---

#### POST /api/uploads/courses

Create a new course.

**Auth required:** Yes

**Request Body (JSON):**

```json
{
  "name": "Introduction to AI"
}
```

**Response (200):**

```json
{
  "id": 1,
  "name": "Introduction to AI",
  "upload_count": 0,
  "created_at": "2026-01-10T08:00:00"
}
```

---

#### DELETE /api/uploads/courses/{course_id}

Delete a course. Uploads assigned to this course will have their `course_id` set to null.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `course_id` | integer | The course ID |

**Response (200):**

```json
{
  "detail": "Deleted"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Course not found"` |

---

#### GET /api/uploads/tags/list

List all tags for the current user.

**Auth required:** Yes

**Response (200):**

```json
[
  {
    "id": 1,
    "name": "important"
  }
]
```

---

#### POST /api/uploads/tags

Create a new tag. If a tag with the same name already exists, the existing tag is returned.

**Auth required:** Yes

**Request Body (JSON):**

```json
{
  "name": "important"
}
```

**Response (200):**

```json
{
  "id": 1,
  "name": "important"
}
```

---

#### DELETE /api/uploads/tags/{tag_id}

Delete a tag.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `tag_id` | integer | The tag ID |

**Response (200):**

```json
{
  "detail": "Deleted"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Tag not found"` |

---

#### POST /api/uploads/{upload_id}/tags/{tag_id}

Add a tag to an upload.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |
| `tag_id` | integer | The tag ID |

**Response (200):**

```json
{
  "detail": "Tag added"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |
| 404 | `"Tag not found"` |

---

#### DELETE /api/uploads/{upload_id}/tags/{tag_id}

Remove a tag from an upload.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |
| `tag_id` | integer | The tag ID |

**Response (200):**

```json
{
  "detail": "Tag removed"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |
| 404 | `"Tag not found"` |

---

### Chat (`/api/chat`)

---

#### POST /api/chat/{upload_id}

Send a message to the AI assistant about a specific upload. The AI uses the upload's transcript as context. Creates a new conversation if `conversation_id` is not provided, or continues an existing one.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID to chat about |

**Request Body (JSON):**

```json
{
  "message": "Can you explain the main concept from this lecture?",
  "conversation_id": null
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | Yes | The user's message |
| `conversation_id` | integer | No | Existing conversation ID to continue (null creates a new conversation) |

**Response (200):**

```json
{
  "id": 42,
  "role": "assistant",
  "content": "The main concept discussed in this lecture is...",
  "created_at": "2026-01-15T10:35:00"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |
| 400 | `"Upload has no transcript yet"` |
| 404 | `"Conversation not found"` |

---

#### GET /api/chat/{upload_id}/conversations

List all conversations for a specific upload.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |

**Response (200):**

```json
[
  {
    "id": 1,
    "upload_id": 1,
    "title": "Can you explain the main concept...",
    "created_at": "2026-01-15T10:30:00",
    "messages": []
  }
]
```

Note: The `messages` array is populated when retrieving a single conversation.

---

#### GET /api/chat/{upload_id}/conversations/{conv_id}

Get a specific conversation with all its messages.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |
| `conv_id` | integer | The conversation ID |

**Response (200):**

```json
{
  "id": 1,
  "upload_id": 1,
  "title": "Can you explain the main concept...",
  "created_at": "2026-01-15T10:30:00",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Can you explain the main concept from this lecture?",
      "created_at": "2026-01-15T10:30:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "The main concept discussed in this lecture is...",
      "created_at": "2026-01-15T10:30:05"
    }
  ]
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Conversation not found"` |

---

#### DELETE /api/chat/{upload_id}/conversations/{conv_id}

Delete a conversation and all its messages.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |
| `conv_id` | integer | The conversation ID |

**Response (200):**

```json
{
  "detail": "Conversation deleted"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Conversation not found"` |

---

### Share (`/api/share`)

---

#### POST /api/share/

Share an upload with another user or a study group.

**Auth required:** Yes

**Request Body (JSON):**

```json
{
  "upload_id": 1,
  "shared_with": 2,
  "group_id": null,
  "message": "Check out these notes!"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `upload_id` | integer | Yes | The upload to share |
| `shared_with` | integer | No | User ID to share with (null for public/group share) |
| `group_id` | integer | No | Study group ID to share with |
| `message` | string | No | Optional message to include |

**Response (200):**

```json
{
  "id": 1,
  "upload_id": 1,
  "shared_by": 1,
  "shared_with": 2,
  "group_id": null,
  "message": "Check out these notes!",
  "created_at": "2026-01-15T10:30:00",
  "filename": "lecture-notes.pdf",
  "owner_name": "johndoe"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found or not yours"` |

---

#### GET /api/share/shared-with-me

List all uploads shared with the current user (including public shares).

**Auth required:** Yes

**Response (200):**

```json
[
  {
    "id": 1,
    "upload_id": 1,
    "shared_by": 2,
    "shared_with": 1,
    "group_id": null,
    "message": "Check out these notes!",
    "created_at": "2026-01-15T10:30:00",
    "filename": "lecture-notes.pdf",
    "owner_name": "janedoe"
  }
]
```

---

#### DELETE /api/share/{share_id}

Remove a share. Only the user who created the share can delete it.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `share_id` | integer | The share ID |

**Response (200):**

```json
{
  "detail": "Share removed"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Share not found"` |

---

#### POST /api/share/{upload_id}/comments

Add a comment to a shared upload.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |

**Request Body (JSON):**

```json
{
  "content": "Great summary of the topic!"
}
```

**Response (200):**

```json
{
  "id": 1,
  "upload_id": 1,
  "user_id": 1,
  "content": "Great summary of the topic!",
  "created_at": "2026-01-15T10:30:00",
  "username": "johndoe"
}
```

---

#### GET /api/share/{upload_id}/comments

List all comments on an upload, ordered by creation time (ascending).

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |

**Response (200):**

```json
[
  {
    "id": 1,
    "upload_id": 1,
    "user_id": 1,
    "content": "Great summary of the topic!",
    "created_at": "2026-01-15T10:30:00",
    "username": "johndoe"
  }
]
```

---

#### DELETE /api/share/comments/{comment_id}

Delete a comment. Only the comment author can delete it.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `comment_id` | integer | The comment ID |

**Response (200):**

```json
{
  "detail": "Comment deleted"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Comment not found"` |

---

#### POST /api/share/groups

Create a new study group. The creator is automatically added as the owner.

**Auth required:** Yes

**Request Body (JSON):**

```json
{
  "name": "CS101 Study Group",
  "description": "Study group for Computer Science 101"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Group name |
| `description` | string | No | Group description |

**Response (200):**

```json
{
  "id": 1,
  "name": "CS101 Study Group",
  "description": "Study group for Computer Science 101",
  "owner_id": 1,
  "created_at": "2026-01-15T10:30:00",
  "member_count": 1,
  "owner_name": "johndoe"
}
```

---

#### GET /api/share/groups

List study groups the current user is a member of.

**Auth required:** Yes

**Response (200):**

```json
[
  {
    "id": 1,
    "name": "CS101 Study Group",
    "description": "Study group for Computer Science 101",
    "owner_id": 1,
    "created_at": "2026-01-15T10:30:00",
    "member_count": 5,
    "owner_name": "johndoe"
  }
]
```

---

#### GET /api/share/groups/all

List all study groups (discoverable by any authenticated user).

**Auth required:** Yes

**Response (200):** Same format as `GET /api/share/groups`.

---

#### GET /api/share/groups/{group_id}/members

List all members of a study group. Only accessible to group members.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `group_id` | integer | The group ID |

**Response (200):**

```json
[
  {
    "id": 1,
    "user_id": 1,
    "role": "owner",
    "joined_at": "2026-01-15T10:30:00",
    "username": "johndoe"
  },
  {
    "id": 2,
    "user_id": 3,
    "role": "member",
    "joined_at": "2026-01-16T09:00:00",
    "username": "janedoe"
  }
]
```

**Error Responses:**

| Status | Detail |
|---|---|
| 403 | `"Not a member of this group"` |

---

#### POST /api/share/groups/{group_id}/join

Join a study group.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `group_id` | integer | The group ID |

**Response (200):**

```json
{
  "detail": "Joined group"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Group not found"` |
| 400 | `"Already a member"` |

---

#### POST /api/share/groups/{group_id}/leave

Leave a study group. The group owner cannot leave; they must delete the group instead.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `group_id` | integer | The group ID |

**Response (200):**

```json
{
  "detail": "Left group"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Not a member"` |
| 400 | `"Owner cannot leave. Delete the group instead."` |

---

#### DELETE /api/share/groups/{group_id}

Delete a study group. Only the group owner can delete it. All shares associated with the group are also removed.

**Auth required:** Yes

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `group_id` | integer | The group ID |

**Response (200):**

```json
{
  "detail": "Group deleted"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Group not found or not owner"` |

---

### Admin (`/api/admin`)

All admin endpoints require the authenticated user to have admin privileges (`is_admin: true`). Non-admin users will receive a 403 Forbidden response.

---

#### GET /api/admin/users

List all users in the system with their upload counts.

**Auth required:** Yes (Admin only)

**Response (200):**

```json
[
  {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "is_admin": false,
    "is_active": true,
    "created_at": "2026-01-10T08:00:00",
    "upload_count": 12
  }
]
```

---

#### PATCH /api/admin/users/{user_id}/toggle

Toggle a user's active status (enable/disable). Admins cannot disable themselves.

**Auth required:** Yes (Admin only)

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `user_id` | integer | The user ID |

**Response (200):**

```json
{
  "id": 2,
  "is_active": false
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"User not found"` |
| 400 | `"Cannot disable yourself"` |

---

#### DELETE /api/admin/users/{user_id}

Delete a user and all their uploaded files from disk. Admins cannot delete themselves.

**Auth required:** Yes (Admin only)

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `user_id` | integer | The user ID |

**Response (200):**

```json
{
  "detail": "User deleted"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"User not found"` |
| 400 | `"Cannot delete yourself"` |

---

#### GET /api/admin/uploads

List all uploads across all users. Supports filtering.

**Auth required:** Yes (Admin only)

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `search` | string | null | Filter by filename (case-insensitive partial match) |
| `status` | string | null | Filter by status |
| `user_id` | integer | null | Filter by user ID |

**Response (200):**

```json
[
  {
    "id": 1,
    "filename": "lecture-notes.pdf",
    "file_type": "pdf",
    "file_size": 204800,
    "status": "Completed",
    "created_at": "2026-01-15T10:30:00",
    "username": "johndoe"
  }
]
```

Note: Results are limited to 200 entries.

---

#### DELETE /api/admin/uploads/{upload_id}

Delete any upload (regardless of owner) and remove the file from disk.

**Auth required:** Yes (Admin only)

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `upload_id` | integer | The upload ID |

**Response (200):**

```json
{
  "detail": "Upload deleted"
}
```

**Error Responses:**

| Status | Detail |
|---|---|
| 404 | `"Upload not found"` |

---

#### GET /api/admin/stats

Get system-wide statistics.

**Auth required:** Yes (Admin only)

**Response (200):**

```json
{
  "total_users": 50,
  "total_uploads": 320,
  "total_storage_mb": 1024.5,
  "uploads_by_status": {
    "Completed": 280,
    "Pending": 15,
    "Processing": 5,
    "Failed": 20
  },
  "recent_users": [
    {
      "id": 50,
      "username": "newuser",
      "email": "new@example.com",
      "is_admin": false,
      "is_active": true,
      "created_at": "2026-02-06T14:00:00",
      "upload_count": 0
    }
  ]
}
```

---

#### GET /api/admin/settings

Get current system settings.

**Auth required:** Yes (Admin only)

**Response (200):**

```json
{
  "max_uploads_per_user": 50,
  "max_upload_size_mb": 25,
  "max_audio_minutes": 60,
  "max_pdf_pages": 200
}
```

---

#### PATCH /api/admin/settings

Update system settings. All fields are optional; only provided fields are updated.

**Auth required:** Yes (Admin only)

**Request Body (JSON):**

```json
{
  "max_uploads_per_user": 100,
  "max_upload_size_mb": 50,
  "max_audio_minutes": 120,
  "max_pdf_pages": 500
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `max_uploads_per_user` | integer | No | Maximum uploads per user |
| `max_upload_size_mb` | integer | No | Maximum file size in MB |
| `max_audio_minutes` | integer | No | Maximum audio duration in minutes |
| `max_pdf_pages` | integer | No | Maximum PDF page count |

**Response (200):** Same format as `GET /api/admin/settings`.
