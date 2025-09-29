# giskard

An empathetic assistant and coach. 

Helps me get stuff done, better. 

Continuously improving. 

Follows the laws of robotics.


## 🚀 Quick Start:

```bash
./start_giskard.sh
```

This will start the Flask API backend with proper environment management!

## ✨ Features

### **Core Functionality**
- **Beautiful Design**: Clean, modern interface inspired by Todoist
- **Smart Navigation**: Sidebar with Inbox, Today, Upcoming, and Completed views
- **Task Management**: Add, edit, start, stop, and complete tasks
- **Drag & Drop**: Intuitive task reordering with smooth animations
- **Modal Interface**: Beautiful popups for adding and editing tasks
- **Real-time Updates**: Auto-refreshes every 30 seconds
- **Keyboard Shortcuts**: Cmd+Enter to save, ESC to close modals

### **Technical Excellence**
- **Modular Architecture**: Clean separation of concerns
- **ES6 Modules**: Modern JavaScript with proper imports/exports
- **Type Safety**: JSDoc annotations throughout
- **Input Validation**: Client-side sanitization and validation
- **Performance Optimized**: GPU acceleration and efficient rendering
- **Error Handling**: Robust error boundaries and user feedback

## 🏗️ Architecture

### **Backend (Python/Flask API)**
```
app.py (30 lines)              # API-only entry point
├── models/
│   └── task_db.py            # Database task model
├── api/
│   └── routes_v2.py          # Clean REST API endpoints
└── utils/
    ├── classification_manager.py  # Task classification system
    └── classification_service.py  # LLM classification service
```

### **Frontend (Tauri Desktop App)**
```
giskard-desktop/src/
├── index.html                # Main UI template
├── css/style.css            # Complete styling
├── js/
│   ├── app.js               # Application entry point
│   └── modules/
│       ├── TaskManager.js   # Main orchestrator
│       ├── ChatManager.js   # AI coaching interface
│       ├── APIClient.js     # HTTP requests with validation
│       ├── UIManager.js     # View switching & UI state
│       ├── TaskList.js      # Task rendering & interactions
│       ├── DragDropManager.js # Drag & drop functionality
│       ├── Modal.js         # Reusable modal components
│       └── Notification.js  # Toast notification system
└── src-tauri/               # Rust backend for desktop
```

### **Key Improvements from Refactoring**
- **Simplified Architecture**: Removed web UI, focused on Tauri desktop app
- **Single Source of Truth**: All frontend code consolidated in Tauri directory
- **API-Only Backend**: Flask serves only API endpoints, no template rendering
- **Reduced Complexity**: ~40% reduction in codebase size
- **Cleaner Maintenance**: No duplicate code between web and desktop versions

## 📖 Developer Guide

### **Adding New Features**

1. **New API Endpoint**: Add to `api/routes_v2.py`
2. **New UI Component**: Create in `static/js/modules/`
3. **New Task Property**: Extend `models/task_db.py`

### **Module Communication**
The application uses event-driven communication between modules:

```javascript
// Emit custom events
document.dispatchEvent(new CustomEvent('task:complete', { 
    detail: { task } 
}));

// Listen for events
document.addEventListener('task:complete', (e) => {
    this.handleTaskComplete(e.detail.task);
});
```

### **API Client Usage**
```javascript
import APIClient from './modules/APIClient.js';

const api = new APIClient();

// All methods return { success: boolean, data?: any, error?: string }
const result = await api.addTask('Buy groceries', 'Milk, eggs, bread');
if (result.success) {
    console.log('Task created!');
} else {
    console.error(result.error);
}
```

### **File Structure**
```
giskard/
├── app.py                    # Flask API entry point
├── models/                   # Data models
├── api/                      # API endpoints
├── utils/                    # Utilities
├── giskard-desktop/          # Tauri desktop app
│   ├── src/
│   │   ├── index.html       # Main UI template
│   │   ├── css/style.css    # Complete styling
│   │   └── js/              # Frontend modules
│   └── src-tauri/           # Rust backend
├── start_giskard.sh         # Single startup script
└── data/
    ├── giskard.db                  # SQLite database
    └── classification_predictions_log.txt  # AI classification logs
```

## 🔧 Configuration

### **Environment Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode
python app.py

# Or use the start script
./start.sh
```

### **Todo.txt Format**
- **Open tasks**: `Task title | Description | 1`
- **In progress**: `Task title | Description | 1 status:in_progress`
- **Completed**: `x 2024-01-15 Task title | Description | 1`

## 🛠️ Development

### **Code Quality Standards**
- **JSDoc**: Comprehensive API documentation
- **Input Validation**: Client and server-side validation
- **Error Handling**: Graceful error recovery
- **Performance**: GPU-accelerated animations
- **Security**: Input sanitization and length limits

### **Testing**
```bash
# Test API endpoints
curl http://localhost:5001/api/tasks

# Test frontend modules in browser console
window.TodoApp
```

### **Contributing**
1. Follow the modular architecture patterns
2. Add JSDoc documentation for new functions
3. Include input validation for user inputs
4. Use event-driven communication between modules
5. Maintain single responsibility principle

## 📈 Performance Features

- **Lazy Loading**: ES6 modules loaded on-demand
- **GPU Acceleration**: CSS transforms for smooth animations
- **Smart Refresh**: Only updates when data changes
- **Efficient Rendering**: Minimal DOM manipulation
- **Event Delegation**: Optimized event handling

## 🔒 Security Features

- **Input Sanitization**: Client-side string trimming and length limits
- **Type Validation**: Strict parameter type checking
- **XSS Prevention**: Proper HTML escaping
- **CSRF Protection**: Safe API patterns

---

**Built with modern web standards and clean architecture principles.**