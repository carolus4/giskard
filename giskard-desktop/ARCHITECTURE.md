# Giskard Desktop Architecture

## Overview

Giskard Desktop follows a **layered architecture** that mirrors the backend API design, ensuring consistency between the UI client and the Python agent when accessing task data.

```
┌─────────────────────────────────────────────────────────┐
│  Presentation Layer (UI Components)                     │
│  - GitHubLikeEditor, TaskList, etc.                    │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Application Layer (Managers)                           │
│  - TaskManager: Business logic & orchestration          │
│  - PageManager: Page navigation & UI state             │
│  - TaskDataManager: Data collection & validation       │
└─────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│  API Layer (APIClient)                                  │
│  - HTTP client for backend API                          │
└─────────────────────────────────────────────────────────┘
                      ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│  Backend API (Python Flask)                             │
│  - routes.py: REST endpoints                            │
│  - TaskDB: Database model                               │
└─────────────────────────────────────────────────────────┘
```

---

## Core Principles

### 1. **Separation of Concerns**
Each layer has a single, well-defined responsibility:
- **UI Components**: Render and capture user input
- **Managers**: Coordinate business logic and data flow
- **TaskDataManager**: Centralize data access and validation
- **APIClient**: Handle HTTP communication

### 2. **Encapsulation**
- Components don't access each other's internal state directly
- Data access goes through public APIs (e.g., `TaskDataManager.getCurrentTaskData()`)
- Implementation details are hidden behind clean interfaces

### 3. **Consistency with Backend**
The frontend mirrors backend patterns:

| Backend Pattern | Frontend Equivalent |
|----------------|---------------------|
| `TaskDB` model | `TaskDataManager` |
| `TaskDB.to_dict()` | `TaskDataManager.getCurrentTaskData()` |
| Route validation | `TaskDataManager.validateTaskData()` |
| Partial updates | `TaskDataManager.getChangedFields()` |

---

## Key Components

### TaskDataManager

**Location:** `src/js/modules/TaskDataManager.js`

**Purpose:** Single source of truth for collecting task data from the UI

**Key Methods:**
```javascript
// Get current task data from UI
getCurrentTaskData() → { title, description }

// Get only changed fields (for partial updates)
getChangedFields(originalTask) → { title?, description? }

// Validate data before API submission
validateTaskData(data) → validatedData | throws Error

// Prepare data for API (collect + validate)
prepareForAPI(overrides) → API-ready data
```

**Why it exists:**
- Prevents direct coupling between TaskManager and PageManager
- Centralizes validation rules (mirrors backend)
- Makes it easy to add new task fields in the future
- Single place to fix data collection bugs

**Usage Example:**
```javascript
// ❌ OLD WAY (tight coupling)
const description = this.pageManager.githubEditor.getContent();

// ✅ NEW WAY (encapsulated)
const taskData = this.pageManager.taskDataManager.getCurrentTaskData();
```

---

### PageManager

**Location:** `src/js/modules/PageManager.js`

**Purpose:** Manage page navigation and UI state for the detail page

**Key Responsibilities:**
- Show/hide different pages (task list, task detail, settings)
- Initialize UI components (GitHubLikeEditor, etc.)
- Bind real-time save handlers
- Own the `TaskDataManager` instance

**Relationship with TaskDataManager:**
```javascript
class PageManager {
    constructor() {
        this.taskDataManager = new TaskDataManager(this);
    }
}
```

---

### TaskManager

**Location:** `src/js/modules/TaskManager.js`

**Purpose:** Orchestrate all task operations and business logic

**Key Responsibilities:**
- Handle task CRUD operations via API
- Coordinate status changes
- Manage task lists and state
- Trigger classifications

**Using TaskDataManager:**
```javascript
// When status changes, save current edits first
const currentData = this.pageManager.taskDataManager.getCurrentTaskData();
await this.api.updateTask(taskId, currentData);
```

---

## Data Flow Examples

### Example 1: User Edits Title

```
1. User types in #detail-title input
   ↓
2. PageManager titleInput listener fires (after 1s debounce)
   ↓
3. PageManager.taskDataManager.getCurrentTaskData()
   → Collects: { title: "New Title", description: "..." }
   ↓
4. PageManager._debouncedUpdateTask(taskId, data)
   ↓
5. APIClient.updateTask(taskId, data)
   ↓
6. Backend API PUT /api/tasks/:id
   ↓
7. TaskDB.save() → Logs to task_history
```

### Example 2: User Changes Status

```
1. User clicks status dropdown (open → in_progress)
   ↓
2. TaskManager._handleStatusChangeFromPage({ taskId, status })
   ↓
3. TaskManager gets current data to save edits:
   currentData = pageManager.taskDataManager.getCurrentTaskData()
   ↓
4. TaskManager saves current state:
   api.updateTask(taskId, currentData)
   ↓
5. TaskManager changes status:
   api.updateTaskStatus(taskId, status)
   ↓
6. Backend updates task and logs history
```

---

## Adding New Task Fields

When adding a new field (e.g., `priority`):

### 1. Update TaskDataManager
```javascript
getCurrentTaskData() {
    return {
        title: this._getTitle(),
        description: this._getDescription(),
        priority: this._getPriority()  // NEW
    };
}

_getPriority() {
    const prioritySelect = document.getElementById('priority-select');
    return prioritySelect?.value || 'medium';
}
```

### 2. Update Validation
```javascript
validateTaskData(data) {
    // ... existing validation

    if (data.priority !== undefined) {
        if (!['low', 'medium', 'high'].includes(data.priority)) {
            throw new Error('Invalid priority value');
        }
        validated.priority = data.priority;
    }

    return validated;
}
```

### 3. That's it!
- All existing code automatically includes the new field
- No need to update TaskManager, PageManager save handlers, etc.
- Validation is centralized

---

## Benefits of This Architecture

### ✅ Maintainability
- Clear separation of concerns
- Easy to find where data collection happens (one file)
- Changes in one layer don't cascade

### ✅ Testability
- TaskDataManager can be tested in isolation
- Easy to mock dependencies
- Unit tests don't require full DOM

### ✅ Extensibility
- Adding fields is straightforward
- New validation rules in one place
- Can easily add features like:
  - Field-level change tracking
  - Undo/redo support
  - Offline editing

### ✅ Consistency
- Frontend mirrors backend patterns
- Same validation rules client and server
- Reduces impedance mismatch

### ✅ Bug Prevention
- No more "forgot to include description" bugs
- Single source of truth for data collection
- TypeScript-ready (can add types later)

---

## Migration Guide

### Before (❌ Problematic)
```javascript
// TaskManager.js - Scattered data access
const title = titleInput.value.trim();
const description = this.pageManager.githubEditor.getContent();
// Oops! Forgot to check if githubEditor exists
```

### After (✅ Clean)
```javascript
// TaskManager.js - Centralized via TaskDataManager
const taskData = this.pageManager.taskDataManager.getCurrentTaskData();
// All edge cases handled inside TaskDataManager
```

---

## Future Improvements

### 1. TypeScript Migration
```typescript
interface TaskData {
    title: string;
    description: string;
    project?: string;
    categories?: string[];
}

class TaskDataManager {
    getCurrentTaskData(): TaskData { ... }
}
```

### 2. State Management
Add a reactive state layer (like MobX or Zustand) for:
- Real-time synchronization across views
- Undo/redo support
- Optimistic updates

### 3. Field Decorators
```javascript
@required
@maxLength(200)
title: string;

@optional
@markdown
description: string;
```

---

## Testing

### Unit Tests
```javascript
// test/TaskDataManager.test.js
import TaskDataManager from '../src/js/modules/TaskDataManager.js';

test('validates empty title', () => {
    const manager = new TaskDataManager(mockPageManager);
    expect(() => manager.validateTaskData({ title: '' }))
        .toThrow('Title cannot be empty');
});
```

### Integration Tests
Open `test_task_data_manager.html` in a browser to run integration tests.

---

## Common Patterns

### Pattern 1: Saving Current State
```javascript
const taskData = this.pageManager.taskDataManager.getCurrentTaskData();
await this.api.updateTask(taskId, taskData);
```

### Pattern 2: Partial Updates
```javascript
const changes = this.pageManager.taskDataManager.getChangedFields(originalTask);
if (Object.keys(changes).length > 0) {
    await this.api.updateTask(taskId, changes);
}
```

### Pattern 3: Validated Creation
```javascript
try {
    const taskData = this.pageManager.taskDataManager.prepareForAPI();
    await this.api.createTask(taskData);
} catch (error) {
    Notification.error(error.message);
}
```

---

## Debugging

### Check Current Data
```javascript
// In browser console
window.__giskardApp.taskManager.pageManager.taskDataManager.getCurrentTaskData()
```

### Validate Current State
```javascript
window.__giskardApp.taskManager.pageManager.taskDataManager.isValid()
window.__giskardApp.taskManager.pageManager.taskDataManager.getValidationErrors()
```

---

## Summary

The TaskDataManager architecture:
- **Mirrors backend design** for consistency
- **Centralizes data access** to prevent bugs
- **Encapsulates complexity** for maintainability
- **Enables future growth** with minimal refactoring

This design ensures that whether you're using the Tauri desktop UI or the Python agent, task data flows through clean, well-defined interfaces that are easy to understand, test, and extend.
