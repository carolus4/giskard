# 🚀 Giskard - AI-Powered Productivity Coach

A beautiful desktop productivity app that combines task management with intelligent coaching powered by llama3.1:8b via Ollama.

## ✨ Features Completed

### 📋 Task Management
- ✅ **Complete Todo System** - Full CRUD operations with todo.txt backend
- ✅ **Drag & Drop Reordering** - Intuitive task prioritization
- ✅ **Task Status Management** - Open, In Progress, and Completed states
- ✅ **Detailed Task Views** - Rich task editing with descriptions
- ✅ **Today/Inbox/Completed Views** - Organized task perspectives

### 💬 AI Coaching Assistant
- ✅ **Chat Interface** - Beautiful tabbed layout (Tasks | Chat)
- ✅ **Ollama Integration** - Powered by llama3.1:8b local AI model
- ✅ **Context-Aware Coaching** - AI knows your current tasks and provides personalized advice
- ✅ **Persistent Chat History** - Conversations saved locally
- ✅ **Productivity Personality** - Supportive but direct coaching style
- ✅ **Task Integration** - AI can see and comment on your actual work

### 🎨 Beautiful UI
- ✅ **OpenWebUI-Inspired Design** - Clean, lightweight, modern interface
- ✅ **Responsive Layout** - Works great on different screen sizes
- ✅ **Smooth Animations** - Polished user experience
- ✅ **Tauri Desktop App** - Native performance with web technologies

## 🏗️ Architecture

```
Frontend (Tauri + Vanilla JS)
├── TaskManager - Handles all task operations
├── ChatManager - Manages AI conversations
├── UIManager - Controls views and navigation
└── DragDropManager - Drag & drop functionality

Backend (Flask API)
├── Task Management Routes - CRUD operations
├── Chat Integration Route - AI coaching endpoint
└── todo.txt File Backend - Single source of truth

AI Integration
└── Ollama (llama3.1:8b) - Local AI coaching
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Rust (for Tauri)
- Ollama with llama3.1:8b model

### Setup & Run

1. **Start Ollama & Pull Model:**
   ```bash
   ollama serve
   ollama pull llama3.1:8b
   ```

2. **Start Flask Backend:**
   ```bash
   cd /path/to/giskard
   python app.py
   ```

3. **Start Desktop App:**
   ```bash
   cd giskard-desktop
   npm run tauri dev
   ```

## 💡 Usage

### Task Management
- **Add tasks** via the red "Add task" button
- **Drag & drop** to reorder priorities
- **Click tasks** to open detailed editing
- **Use checkboxes** to mark complete
- **Play/pause buttons** to start/stop work

### AI Coaching
- **Switch to Chat tab** to access Giscard coach
- **Ask for help** with prioritization, motivation, or productivity
- **Get personalized advice** based on your actual tasks
- **Use suggestions** or ask custom questions
- **Chat history** is automatically saved

## 🤖 AI Coaching Examples

- *"Help me prioritize my tasks"* - Get smart prioritization based on your current work
- *"I'm feeling overwhelmed"* - Receive supportive advice and actionable strategies
- *"What should I focus on today?"* - Get recommendations for daily planning
- *"How do I tackle this large project?"* - Break down complex work into manageable steps

## 🎯 Key Benefits

1. **Local & Private** - All data stays on your machine
2. **Context-Aware** - AI knows your actual tasks, not generic advice
3. **Productivity-Focused** - Built specifically for getting things done
4. **Beautiful & Fast** - Native desktop performance
5. **Simple Todo.txt Backend** - Easy to backup, migrate, or integrate

## 📁 File Structure

```
giskard/
├── app.py                 # Flask backend entry point
├── api/routes.py         # API endpoints (tasks + chat)
├── models/task.py        # Task data models
├── utils/file_manager.py # todo.txt file handling
├── todo.txt              # Your tasks (single source of truth)
├── giskard-desktop/      # Tauri desktop app
│   ├── src/
│   │   ├── index.html    # UI structure
│   │   ├── css/style.css # Beautiful styling
│   │   └── js/
│   │       ├── app.js    # Main app entry
│   │       └── modules/  # Modular JavaScript
│   │           ├── TaskManager.js
│   │           ├── ChatManager.js
│   │           └── ...
└── requirements.txt      # Python dependencies
```

## 🔮 What's Next

The core vision is complete! You now have:
- ✅ Beautiful task management 
- ✅ AI-powered productivity coaching
- ✅ Local, private, and fast
- ✅ Todo.txt single source of truth

**Giskard** is ready to be your intelligent productivity companion! 🎉

---

*Built with ❤️ using Tauri, Flask, and Ollama*
