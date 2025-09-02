#!/usr/bin/env python3
"""
mini_todo - the smallest possible todo.txt manager

scope (v0.2
- single file: todo.txt
- commands:
    - init
    - add "..."
    - list
    - start 1 (mark as in progress)
    - stop 1 (remove in progress status)
    - done 1
- format:
    "Task title" (open)
    "Task title status:in_progress" (in progress)
    "x 2024-01-15 Task title" (completed with date)

Usage:
    ./mini_todo.py init
    ./mini_todo.py add "Write a blog post"
    ./mini_todo.py list
    ./mini_todo.py start 1
    ./mini_todo.py stop 1
    ./mini_todo.py done 2
"""
import argparse
from pathlib import Path
import sys
from datetime import datetime

TODO_PATH = Path("todo.txt")

def ensure_file():
    if not TODO_PATH.exists():
        TODO_PATH.write_text("", encoding="utf-8")

def read_lines():
    ensure_file()
    content = TODO_PATH.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return content.splitlines()

def write_lines(lines):
    if lines:
        TODO_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        TODO_PATH.write_text("", encoding="utf-8")

def cmd_init():
    ensure_file()
    print(f"Initialized {TODO_PATH}")

def cmd_add(title: str):
    lines = read_lines()
    lines.append(title)
    write_lines(lines)
    print(f"Added: {title}")

def parse_tasks(lines):
    """Return (open tasks, in_progress tasks, done tasks) as lists of (idx_in_file, title)."""
    open_tasks = []
    in_progress_tasks = []
    done_tasks = []
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if line.startswith("x "):
            # Completed task: "x 2024-01-15 Task title" or "x Task title"
            # Extract the task title (skip date if present)
            parts = line[2:].strip().split(" ", 1)
            if len(parts) >= 2 and parts[0].count('-') == 2:
                # Has date format YYYY-MM-DD
                title = parts[1]
            else:
                # No date, everything after "x " is the title
                title = line[2:].strip()
            done_tasks.append((idx, title))
        elif "status:in_progress" in line:
            # In progress task: "Task title status:in_progress"
            title = line.replace("status:in_progress", "").strip()
            in_progress_tasks.append((idx, title))
        else:
            # Open task: just the plain text
            open_tasks.append((idx, line))
    return open_tasks, in_progress_tasks, done_tasks

def cmd_list():
    lines = read_lines()
    open_tasks, in_progress_tasks, done_tasks = parse_tasks(lines)
    if not open_tasks and not in_progress_tasks and not done_tasks:
        print("(empty) — add something with: ./mini_todo add 'Task'")
        return
    
    # Use continuous numbering matching the done command order
    task_num = 1
    if in_progress_tasks:
        print("In Progress:")
        for _, title in in_progress_tasks:
            print(f"  → {task_num}. {title}")
            task_num += 1
    if open_tasks:
        if in_progress_tasks:
            print("\nOpen:")
        else:
            print("Open:")
        for _, title in open_tasks:
            print(f"  {task_num}. {title}")
            task_num += 1
    if done_tasks:
        print("\nDone:")
        for _, title in done_tasks:
            print(f"  - {title}")

def cmd_done(n: int):
    lines = read_lines()
    open_tasks, in_progress_tasks, _ = parse_tasks(lines)
    # Match the display order: in_progress first, then open
    all_active_tasks = in_progress_tasks + open_tasks
    if n < 1 or n > len(all_active_tasks):
        print(f"Choose a number 1..{len(all_active_tasks)} from 'In Progress' or 'Open' list.")
        sys.exit(1)
    file_idx, title = all_active_tasks[n-1]
    completion_date = datetime.now().strftime("%Y-%m-%d")
    lines[file_idx] = f"x {completion_date} {title}"
    write_lines(lines)
    print(f"Done: {title}")

def cmd_start(n: int):
    lines = read_lines()
    open_tasks, _, _ = parse_tasks(lines)
    if n < 1 or n > len(open_tasks):
        print(f"Choose a number 1..{len(open_tasks)} from 'Open' list.")
        sys.exit(1)
    file_idx, title = open_tasks[n-1]
    lines[file_idx] = f"{title} status:in_progress"
    write_lines(lines)
    print(f"Started: {title}")

def cmd_stop(n: int):
    lines = read_lines()
    _, in_progress_tasks, _ = parse_tasks(lines)
    if n < 1 or n > len(in_progress_tasks):
        print(f"Choose a number 1..{len(in_progress_tasks)} from 'In Progress' list.")
        sys.exit(1)
    file_idx, title = in_progress_tasks[n-1]
    lines[file_idx] = title
    write_lines(lines)
    print(f"Stopped: {title}")

def main():
    ap = argparse.ArgumentParser(description="mini todo.txt manager")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("init")

    p_add = sub.add_parser("add")
    p_add.add_argument("title")

    sub.add_parser("list")

    p_done = sub.add_parser("done")
    p_done.add_argument("n", type=int)

    p_start = sub.add_parser("start")
    p_start.add_argument("n", type=int)

    p_stop = sub.add_parser("stop")
    p_stop.add_argument("n", type=int)

    args = ap.parse_args()

    if args.cmd == "init":
        cmd_init()
    elif args.cmd == "add":
        cmd_add(args.title)
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "done":
        cmd_done(args.n)
    elif args.cmd == "start":
        cmd_start(args.n)
    elif args.cmd == "stop":
        cmd_stop(args.n)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
