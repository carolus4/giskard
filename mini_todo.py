#!/usr/bin/env python3
"""
mini_todo - the smallest possible markdown todo manager

scope (v0.1
- single file: todo.md
- commands:
    - init
    - add "..."
    - list
    - done 1
- format:
    "- [ ] Task title" (unchecked)
    "- [x] Task title" (checked)

Usage:
    ./mini_todo.py init
    ./mini_todo.py add "Write a blog post"
    ./mini_todo.py list
    ./mini_todo.py done 2
"""
import argparse
from pathlib import Path
import sys

TODO_PATH = Path("todo.md")
LINE_OPEN = "- [ ] "
LINE_DONE = "- [x] "

HEADER = """# TODO

""" # Kept minimal.

def ensure_file():
    if not TODO_PATH.exists():
        TODO_PATH.write_text(HEADER, encoding="utf-8")

def read_lines():
    ensure_file()
    return TODO_PATH.read_text(encoding="utf-8").splitlines()

def write_lines(lines):
    TODO_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

def cmd_init():
    ensure_file()
    print(f"Initialized {TODO_PATH}")

def cmd_add(title: str):
    lines = read_lines()
    if not lines:
        lines = [HEADER.strip()] # Safety, but shouldn't happen.
    if not lines[0].startswith("#"):
        lines.insert(0, HEADER.strip())
    # apend at end
    lines.append(f"{LINE_OPEN}{title}")
    write_lines(lines)
    print(f"Added: {title}")

def parse_tasks(lines):
    """Return (open tasks, done tasks) as lists of (idx_in_file, title)."""
    open_tasks = []
    done_tasks = []
    for idx, line in enumerate(lines):
        if line.startswith(LINE_OPEN):
            open_tasks.append((idx, line[len(LINE_OPEN):].strip()))
        elif line.startswith(LINE_DONE):
            done_tasks.append((idx, line[len(LINE_DONE):].strip()))
    return open_tasks, done_tasks

def cmd_list():
    lines = read_lines()
    open_tasks, done_tasks = parse_tasks(lines)
    if not open_tasks and not done_tasks:
        print("(empty) — add something with: ./mini_todo add 'Task'")
        return
    if open_tasks:
        print("Open:")
        for n, (_, title) in enumerate(open_tasks, start=1):
            print(f"  {n}. {title}")
    if done_tasks:
        print("\nDone:")
        for n, (_, title) in enumerate(done_tasks, start=1):
            print(f"  - {title}")

def cmd_done(n: int):
    lines = read_lines()
    open_tasks, _ = parse_tasks(lines)
    if n < 1 or n > len(open_tasks):
        print(f"Choose a number 1..{len(open_tasks)} from 'Open' list.")
        sys.exit(1)
    file_idx, title = open_tasks[n-1]
    lines[file_idx] = f"{LINE_DONE}{title}"
    write_lines(lines)
    print(f"Done: {title}")

def main():
    ap = argparse.ArgumentParser(description="mini markdown todo manager")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("init")

    p_add = sub.add_parser("add")
    p_add.add_argument("title")

    sub.add_parser("list")

    p_done = sub.add_parser("done")
    p_done.add_argument("n", type=int)

    args = ap.parse_args()

    if args.cmd == "init":
        cmd_init()
    elif args.cmd == "add":
        cmd_add(args.title)
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "done":
        cmd_done(args.n)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
