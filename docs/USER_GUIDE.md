# Smart Study Assistant - User Guide

## Account Access

### Register

Use the login page to create an account with:

- `username`
- `email`
- `password`

After registration, the frontend logs you in automatically.

### Login

Use your username and password on the login page. The backend also accepts email in the same login field, but the current UI is labeled as `Username`.

## Dashboard

The dashboard is the main workspace for your own uploads.

### Upload materials

You can upload one file or multiple files at once.

Supported file types:

- Documents: `pdf`, `pptx`, `ppt`, `docx`
- Audio: `mp3`, `wav`
- Images: `png`, `jpg`, `jpeg`
- Video: `mp4`, `mov`

Each upload can optionally be assigned to one course.

### Courses

The dashboard includes course management:

- create a course
- delete a course
- assign a course during upload
- filter uploads by course

Deleting a course does not delete the files inside it. It only clears the course assignment from those uploads.

### Upload list controls

The uploads list supports:

- search by filename
- filter by status
- filter by course
- sort by newest, oldest, or filename
- retry failed uploads
- delete uploads

### Public / private visibility

For completed uploads, the dashboard shows a two-state visibility control:

- `Private`
- `Public`

This controls global visibility in the shared materials list.

- `Private` means only you, directly shared users, group members of shared groups, and admins can open the file.
- `Public` means other users can also see it in `Shared With Me`.

## Upload Processing

New uploads move through these statuses:

- `Pending`
- `Processing`
- `Completed`
- `Failed`

Analysis is asynchronous. If uploads stay stuck in `Pending` or `Processing`, the Celery worker is usually not running.

## Upload Detail Page

Open an upload from the dashboard, shared page, group workspace, or admin uploads view.

When the upload is completed, the detail page includes these tabs:

- `Summary`
- `Concepts`
- `Flashcards`
- `Q&A`
- `Graph`
- `Transcript`

### Owner vs read-only access

Owners can:

- edit summary
- edit concepts
- edit flashcards
- mark flashcards as known
- run SM-2 review
- open the share dialog
- export the analysis

Shared users, group members, and admins can still open the same analysis page, but they see `Read Only` and do not get owner-only edit controls.

### Summary

Shows the generated summary. Owners can edit it.

### Concepts

Shows extracted concepts and citations. Owners can edit concept titles and descriptions.

### Flashcards

Shows generated flashcards. Owners can:

- edit question and answer
- mark a card as known
- enter `Review Unknown`
- rate recall with the SM-2 buttons

### Q&A

The Q&A tab lets you ask questions against the current upload.

Access is based on upload read permission, not only ownership. A user who can open the upload can also use Q&A for that upload.

### Graph

The graph tab generates a knowledge graph from the upload content.

### Transcript

Shows the extracted text, OCR result, or transcription used for the analysis.

### Comments

The detail page also includes a comment section below the tabs.

Users with access to the upload can:

- read comments
- post comments
- delete their own comments

## Sharing

Owners can open the `Share` dialog from a completed upload.

### Public visibility

Inside the share dialog, the same file can be toggled between:

- `Private`
- `Public`

This is the same upload-level visibility flag that appears on the dashboard.

### Direct share

Share to a specific user by entering:

- username
- or email

Direct shares can be created with:

- `Read Only`
- `Can Edit`

### Share to group

Share the upload to one of your study groups.

Important rule:

- `Private + shared to group` means only members of that group can access it.
- Sharing to a group does not automatically make the file public.

### Existing shares

The share dialog also shows current direct and group shares and lets the owner remove them.

## Shared With Me

The `Shared` page shows everything the current user can access through sharing:

- direct shares
- public uploads
- files shared into groups you belong to

Each item includes:

- owner
- permission
- share type
- optional message

Use `Open Analysis` to open the same detail page used by the owner.

## Study Groups

The `Groups` page is a group workspace, not just a list.

### Group creation and discovery

You can:

- create a group
- set join mode to `Open join` or `Approval required`
- browse groups you have not joined
- join directly or send a join request

### Invites

The page shows pending invites that you can accept or decline.

### Group workspace

After opening one of your groups, the workspace includes:

- members
- shared files
- group chat
- invite member
- join request review for the owner

### Sharing files to a group

The group workspace does not upload raw files directly from the chat box.

Instead, it lets you share one of your existing completed uploads into the group. Group members can then use `Open Analysis` on that shared file.

### Group chat

Group chat currently supports text messages. When a file is shared into a group, the workspace also posts a message announcing that share.

## Statistics

The `Statistics` page includes:

- total uploads
- completed uploads
- flashcards mastered
- key concepts
- study heatmap
- uploads over time chart
- status distribution chart
- learning progress chart
- forgetting curve chart
- flashcard mastery progress bar
- AI learning path generator
- usage quota summary

The learning path generator works from your completed uploads.

## Admin

The admin UI is available at `/admin`, but the navbar shows the link only for users whose account has `is_admin=true`.

There is no automatic default admin bootstrap in the application. An account must be promoted manually or created as admin in the database.

### Admin tabs

The admin page currently includes:

- `Users`
- `Uploads`
- `Statistics`
- `Settings`

### Admin abilities

Admins can:

- view all users
- enable or disable users
- delete users
- view all uploads
- open any upload analysis page
- toggle upload public visibility
- delete uploads
- view platform statistics
- change upload and processing limits

## Troubleshooting

### Upload completes but analysis is missing

Check that the backend worker is running. Upload analysis depends on Celery.

### Shared file opens in read-only mode

That is expected for users who are not the owner.

### A private file is visible in a group

That is also expected when the owner shared the file into that group. Private means not globally public, not group-hidden.
