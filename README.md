# giskard

An empathetic assistant and coach. 

Helps me get stuff done, better. 

Continuously improving. 

Follows the laws of robotics.

## 🚀  Web UI

Launch the Todoist-inspired web interface:

```bash
./start.sh
```

Then open http://localhost:5000 in your browser for a beautiful, modern task management experience!

## 📱 Features

- **Clean Design**: Interface inspired by Todoist
- **Navigation**: Sidebar with Inbox, Today, Upcoming, and Completed views
- **Task Management**: Add, start, stop, and complete tasks with smooth animations
- **Real-time Updates**: Auto-refreshes to stay in sync
- **Local Data**: Uses `todo.txt` file format

## 🖥️ CLI Usage (Alternative)

Also works with the command line interface:

```bash
python mini_todo.py init
# Initialized todo.txt

python mini_todo.py add "Write blog post"
# Added: Write blog post

python mini_todo.py list
# Open:
#   1. Write blog post

python mini_todo.py done 1
# Done: Write blog post

python mini_todo.py list
# Done:
#   - Write blog post
```

## Todo.txt Format

This tool now follows the todo.txt standard format:
- Open tasks: `Task title`  
- Completed tasks: `x 2024-01-15 Task title` (with completion date)
- No priority tags (as requested)
- Plain text format, not markdown