# Giskard API Documentation

A comprehensive guide to the Giskard backend API endpoints for task management and AI-powered classification.

## 🚀 Quick Start

**Base URL:** `http://localhost:5001/api`

**Content-Type:** `application/json`

**CORS:** Enabled for Tauri desktop app and localhost development

## 📋 API Endpoints

### Task Management

#### Get All Tasks
```http
GET /api/tasks
```

**Description:** Retrieve all tasks grouped by status with counts and metadata.

**Response:**
```json
{
  "tasks": {
    "in_progress": [
      {
        "id": 1,
        "title": "Complete project proposal",
        "description": "Write the technical specification",
        "project": "Work",
        "categories": ["work", "urgent"],
        "status": "in_progress",
        "sort_key": 1,
        "created_at": "2025-09-23T10:48:04.535457",
        "updated_at": "2025-09-23T10:48:04.535664",
        "started_at": "2025-09-23T11:00:00.000000",
        "completed_at": null
      }
    ],
    "open": [...],
    "done": [...]
  },
  "counts": {
    "today": 5,
    "completed_today": 3,
    "completed_yesterday": 2
  },
  "today_date": "Today - Monday Sep 23"
}
```

#### Create Task
```http
POST /api/tasks
```

**Description:** Create a new task with optional project and categories.

**Request Body:**
```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread, and vegetables",
  "project": "Personal",
  "categories": ["shopping", "personal"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Created: Buy groceries",
  "task": {
    "id": 123,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread, and vegetables",
    "project": "Personal",
    "categories": ["shopping", "personal"],
    "status": "open",
    "sort_key": 123,
    "created_at": "2025-09-23T10:48:04.535457",
    "updated_at": "2025-09-23T10:48:04.535664",
    "started_at": null,
    "completed_at": null
  }
}
```

#### Get Specific Task
```http
GET /api/tasks/{id}
```

**Description:** Retrieve a specific task by ID.

**Response:**
```json
{
  "id": 123,
  "title": "Buy groceries",
  "description": "Milk, eggs, bread, and vegetables",
  "project": "Personal",
  "categories": ["shopping", "personal"],
  "status": "open",
  "sort_key": 123,
  "created_at": "2025-09-23T10:48:04.535457",
  "updated_at": "2025-09-23T10:48:04.535664",
  "started_at": null,
  "completed_at": null
}
```

#### Update Task
```http
PUT /api/tasks/{id}
```

**Description:** Update an existing task's properties.

**Request Body:**
```json
{
  "title": "Buy groceries and household items",
  "description": "Milk, eggs, bread, vegetables, and cleaning supplies",
  "project": "Household",
  "categories": ["shopping", "household"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Task updated",
  "task": {
    "id": 123,
    "title": "Buy groceries and household items",
    "description": "Milk, eggs, bread, vegetables, and cleaning supplies",
    "project": "Household",
    "categories": ["shopping", "household"],
    "status": "open",
    "sort_key": 123,
    "created_at": "2025-09-23T10:48:04.535457",
    "updated_at": "2025-09-23T12:30:00.000000",
    "started_at": null,
    "completed_at": null
  }
}
```

#### Delete Task
```http
DELETE /api/tasks/{id}
```

**Description:** Delete a specific task.

**Response:**
```json
{
  "success": true,
  "message": "Deleted: Buy groceries"
}
```

#### Update Task Status
```http
PATCH /api/tasks/{id}/status
```

**Description:** Update a task's status (open, in_progress, done).

**Request Body:**
```json
{
  "status": "in_progress"
}
```

**Valid Status Values:**
- `open` - Task is not started
- `in_progress` - Task is currently being worked on
- `done` - Task is completed

**Response:**
```json
{
  "success": true,
  "message": "Status updated to in_progress",
  "task": {
    "id": 123,
    "title": "Buy groceries",
    "status": "in_progress",
    "started_at": "2025-09-23T12:30:00.000000",
    "updated_at": "2025-09-23T12:30:00.000000"
  }
}
```

#### Reorder Tasks
```http
POST /api/tasks/reorder
```

**Description:** Reorder tasks by providing a list of task IDs in the desired order.

**Request Body:**
```json
{
  "task_ids": [3, 1, 2, 5, 4]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Tasks reordered successfully"
}
```

## 🔧 Response Formats

### Success Response
```json
{
  "success": true,
  "message": "Success message",
  "data": { /* optional response data */ }
}
```

### Error Response
```json
{
  "error": "Error message description"
}
```

## 📊 HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request - Invalid input data |
| `404` | Not Found - Task doesn't exist |
| `500` | Internal Server Error |

## 🚨 Error Handling

### Common Error Scenarios

**Task Not Found (404):**
```json
{
  "error": "Task not found"
}
```

**Invalid Status (400):**
```json
{
  "error": "Invalid status. Must be: open, in_progress, or done"
}
```

**Missing Required Field (400):**
```json
{
  "error": "Task title is required"
}
```

**Empty Title (400):**
```json
{
  "error": "Task title cannot be empty"
}
```

**Invalid Reorder Data (400):**
```json
{
  "error": "task_ids array is required"
}
```

## 🧪 Testing Examples

### Using curl

```bash
# Get all tasks
curl http://localhost:5001/api/tasks

# Create a new task
curl -X POST http://localhost:5001/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "description": "Testing API", "project": "Testing"}'

# Update task status
curl -X PATCH http://localhost:5001/api/tasks/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# Delete a task
curl -X DELETE http://localhost:5001/api/tasks/1
```

### Using JavaScript (Frontend)

```javascript
// Get all tasks
const response = await fetch('http://localhost:5001/api/tasks');
const data = await response.json();

// Create a task
const newTask = await fetch('http://localhost:5001/api/tasks', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'New task',
    description: 'Task description',
    project: 'Work',
    categories: ['urgent']
  })
});

// Update task status
await fetch(`http://localhost:5001/api/tasks/${taskId}/status`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ status: 'done' })
});
```

## 🤖 AI Integration

The API automatically integrates with AI classification:

- **Automatic Classification**: New and updated tasks are automatically classified using AI
- **Background Processing**: Classification happens asynchronously
- **Performance Tracking**: Classification metrics are logged for analysis
- **Ollama Integration**: Uses local Ollama service for AI processing

## 🔒 Security & Validation

- **Input Sanitization**: All text inputs are trimmed and validated
- **Length Limits**: Task titles and descriptions have reasonable length limits
- **Type Validation**: Strict parameter type checking
- **CORS Protection**: Configured for specific origins only

## 📈 Performance Features

- **SQLite Database**: Fast, local database for task storage
- **Efficient Queries**: Optimized database queries for task retrieval
- **Background Processing**: Non-blocking AI classification
- **Caching**: Response caching for improved performance

## 🛠️ Development

### Adding New Endpoints

1. Add route to `api/routes_v2.py`
2. Follow REST conventions (GET, POST, PUT, DELETE, PATCH)
3. Use `APIResponse` helper for consistent responses
4. Add error handling with appropriate status codes
5. Update this documentation

### Database Schema

Tasks are stored in SQLite with the following schema:

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('open','in_progress','done')),
    sort_key INTEGER NOT NULL,
    project TEXT DEFAULT NULL,
    category TEXT DEFAULT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);
```

---

**Last Updated:** September 23, 2025  
**API Version:** v2  
**Backend:** Flask with SQLite  
**Frontend:** Tauri Desktop App
