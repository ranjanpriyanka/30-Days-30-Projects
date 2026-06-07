#!/usr/bin/env python3
"""
CLI Todo App — with file persistence, priorities, due dates, colors, and search.
Usage:
    python todo.py                        # interactive menu
    python todo.py add "Buy groceries"
    python todo.py list
    python todo.py list --filter pending
    python todo.py list --filter completed
    python todo.py complete 2
    python todo.py delete 3
    python todo.py edit 1 "Updated task"
    python todo.py search "groceries"
    python todo.py priority 1 high
"""

import json
import sys
import os
from datetime import datetime, date
from colorama import init, Fore, Style

# Initialize colorama (cross-platform color support)
init(autoreset=True)

# ─── Config ──────────────────────────────────────────────────────────────────

TASKS_FILE = "tasks.json"
PRIORITIES = ["low", "medium", "high"]
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

# ─── File Helpers ─────────────────────────────────────────────────────────────

def load_tasks() -> list:
    """Load tasks from JSON file. Returns empty list if file missing/corrupt."""
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        print(warn("⚠  tasks.json was corrupt — starting fresh."))
        return []

def save_tasks(tasks: list) -> None:
    """Save tasks list to JSON file."""
    try:
        with open(TASKS_FILE, "w") as f:
            json.dump(tasks, f, indent=2)
    except IOError as e:
        print(error(f"Could not save tasks: {e}"))

def next_id(tasks: list) -> int:
    """Generate the next unique task ID."""
    return max((t["id"] for t in tasks), default=0) + 1

# ─── Color Helpers ────────────────────────────────────────────────────────────

def success(msg): return Fore.GREEN + msg
def error(msg):   return Fore.RED + msg
def warn(msg):    return Fore.YELLOW + msg
def info(msg):    return Fore.CYAN + msg
def bold(msg):    return Style.BRIGHT + msg
def dim(msg):     return Style.DIM + msg

PRIORITY_COLOR = {
    "low":    Fore.BLUE,
    "medium": Fore.YELLOW,
    "high":   Fore.RED,
}

# ─── Display ──────────────────────────────────────────────────────────────────

def format_task(task: dict) -> str:
    """Format a single task as a colored string."""
    tid       = bold(f"[{task['id']:>3}]")
    status    = (Fore.GREEN + "✔ Done   ") if task["status"] == "completed" else (Fore.YELLOW + "○ Pending")
    priority  = PRIORITY_COLOR.get(task["priority"], "") + f"[{task['priority'].upper():<6}]"
    desc      = (dim(task["description"]) if task["status"] == "completed"
                 else task["description"])

    due_str = ""
    if task.get("due_date"):
        try:
            due = datetime.strptime(task["due_date"], DATE_FORMAT).date()
            today = date.today()
            if task["status"] != "completed":
                if due < today:
                    due_str = Fore.RED + f" ⚑ OVERDUE ({task['due_date']})"
                elif due == today:
                    due_str = Fore.MAGENTA + f" ⚑ Due TODAY"
                else:
                    due_str = dim(f" · due {task['due_date']}")
            else:
                due_str = dim(f" · due {task['due_date']}")
        except ValueError:
            due_str = dim(f" · due {task['due_date']}")

    created = dim(f"  (added {task.get('created_at', '')[:10]})")
    return f"{tid} {status} {Style.RESET_ALL}{priority} {Style.RESET_ALL}{desc}{due_str}{created}"

def print_tasks(tasks: list, filter_by: str = "all") -> None:
    """Print tasks with optional status filter."""
    filtered = tasks
    if filter_by == "pending":
        filtered = [t for t in tasks if t["status"] == "pending"]
    elif filter_by == "completed":
        filtered = [t for t in tasks if t["status"] == "completed"]

    if not filtered:
        print(warn("  No tasks found."))
        return

    total     = len(tasks)
    done      = sum(1 for t in tasks if t["status"] == "completed")
    pending   = total - done
    label     = "" if filter_by == "all" else f" [{filter_by.upper()}]"
    print(info(f"\n  📋  Todo List{label}  ·  {pending} pending  ·  {done} done  ·  {total} total\n"))

    for task in filtered:
        print("  " + format_task(task))
    print()

# ─── Task Operations ──────────────────────────────────────────────────────────

def add_task(tasks: list, description: str,
             priority: str = "medium", due_date: str = None) -> None:
    """Add a new task."""
    description = description.strip()
    if not description:
        print(error("  Task description cannot be empty."))
        return

    priority = priority.lower()
    if priority not in PRIORITIES:
        print(warn(f"  Unknown priority '{priority}'. Using 'medium'."))
        priority = "medium"

    if due_date:
        try:
            datetime.strptime(due_date, DATE_FORMAT)
        except ValueError:
            print(warn(f"  Invalid date '{due_date}' (expected YYYY-MM-DD). Ignoring."))
            due_date = None

    task = {
        "id":          next_id(tasks),
        "description": description,
        "status":      "pending",
        "priority":    priority,
        "due_date":    due_date,
        "created_at":  datetime.now().strftime(DATETIME_FORMAT),
    }
    tasks.append(task)
    save_tasks(tasks)
    print(success(f"  ✔ Task #{task['id']} added: \"{description}\""))

def complete_task(tasks: list, task_id: int) -> None:
    """Mark a task as completed."""
    task = find_task(tasks, task_id)
    if not task:
        return
    if task["status"] == "completed":
        print(warn(f"  Task #{task_id} is already completed."))
        return
    task["status"] = "completed"
    save_tasks(tasks)
    print(success(f"  ✔ Task #{task_id} marked as completed!"))

def delete_task(tasks: list, task_id: int) -> None:
    """Delete a task by ID."""
    task = find_task(tasks, task_id)
    if not task:
        return
    tasks.remove(task)
    save_tasks(tasks)
    print(success(f"  ✔ Task #{task_id} deleted."))

def edit_task(tasks: list, task_id: int, new_description: str) -> None:
    """Edit the description of an existing task."""
    task = find_task(tasks, task_id)
    if not task:
        return
    new_description = new_description.strip()
    if not new_description:
        print(error("  New description cannot be empty."))
        return
    task["description"] = new_description
    save_tasks(tasks)
    print(success(f"  ✔ Task #{task_id} updated."))

def set_priority(tasks: list, task_id: int, priority: str) -> None:
    """Set the priority of a task."""
    task = find_task(tasks, task_id)
    if not task:
        return
    priority = priority.lower()
    if priority not in PRIORITIES:
        print(error(f"  Invalid priority. Choose from: {', '.join(PRIORITIES)}"))
        return
    task["priority"] = priority
    save_tasks(tasks)
    print(success(f"  ✔ Task #{task_id} priority set to {priority.upper()}."))

def search_tasks(tasks: list, query: str) -> None:
    """Search tasks by description (case-insensitive)."""
    query = query.strip().lower()
    results = [t for t in tasks if query in t["description"].lower()]
    if not results:
        print(warn(f"  No tasks found matching \"{query}\"."))
        return
    print(info(f"\n  🔍  Search results for \"{query}\" ({len(results)} found)\n"))
    for task in results:
        print("  " + format_task(task))
    print()

def find_task(tasks: list, task_id: int):
    """Return task by ID, or print error and return None."""
    for t in tasks:
        if t["id"] == task_id:
            return t
    print(error(f"  No task found with ID #{task_id}."))
    return None

# ─── Interactive Menu ─────────────────────────────────────────────────────────

def interactive_menu(tasks: list) -> None:
    """Run the interactive menu loop."""
    print(bold(info("\n  ┌─────────────────────────────┐")))
    print(bold(info("  │     🗒  CLI Todo App          │")))
    print(bold(info("  └─────────────────────────────┘")))

    while True:
        print(info("\n  ─── Menu ──────────────────────"))
        print("  1. Add Task")
        print("  2. View All Tasks")
        print("  3. View Pending Tasks")
        print("  4. View Completed Tasks")
        print("  5. Mark Task as Completed")
        print("  6. Delete Task")
        print("  7. Edit Task")
        print("  8. Set Priority")
        print("  9. Search Tasks")
        print("  0. Exit")
        print(info("  ───────────────────────────────"))

        choice = input("  Choose an option: ").strip()

        if choice == "1":
            desc = input("  Task description: ").strip()
            pri  = input("  Priority [low/medium/high] (default: medium): ").strip() or "medium"
            due  = input("  Due date [YYYY-MM-DD] (optional, press Enter to skip): ").strip() or None
            add_task(tasks, desc, pri, due)

        elif choice == "2":
            print_tasks(tasks)

        elif choice == "3":
            print_tasks(tasks, "pending")

        elif choice == "4":
            print_tasks(tasks, "completed")

        elif choice == "5":
            print_tasks(tasks, "pending")
            tid = prompt_id("  Task ID to complete: ")
            if tid: complete_task(tasks, tid)

        elif choice == "6":
            print_tasks(tasks)
            tid = prompt_id("  Task ID to delete: ")
            if tid: delete_task(tasks, tid)

        elif choice == "7":
            print_tasks(tasks)
            tid  = prompt_id("  Task ID to edit: ")
            if tid:
                new_desc = input("  New description: ").strip()
                edit_task(tasks, tid, new_desc)

        elif choice == "8":
            print_tasks(tasks)
            tid = prompt_id("  Task ID: ")
            if tid:
                pri = input("  New priority [low/medium/high]: ").strip()
                set_priority(tasks, tid, pri)

        elif choice == "9":
            q = input("  Search query: ").strip()
            if q: search_tasks(tasks, q)

        elif choice == "0":
            print(success("\n  👋  Goodbye! Stay productive!\n"))
            break

        else:
            print(warn("  Invalid option. Please choose 0–9."))

def prompt_id(prompt_text: str):
    """Prompt for an integer task ID."""
    raw = input(prompt_text).strip()
    if not raw.isdigit():
        print(error("  Please enter a valid numeric task ID."))
        return None
    return int(raw)

# ─── CLI Entry Point ──────────────────────────────────────────────────────────

def print_help():
    print(f"""
{bold(info('CLI Todo App — Command Reference'))}

  python todo.py                         Interactive menu
  python todo.py add "Task"              Add a task (priority: medium)
  python todo.py add "Task" high         Add a task with priority
  python todo.py add "Task" high 2025-12-31  Add with priority + due date
  python todo.py list                    List all tasks
  python todo.py list pending            List pending tasks
  python todo.py list completed          List completed tasks
  python todo.py complete <id>           Mark task as completed
  python todo.py delete <id>             Delete a task
  python todo.py edit <id> "New text"    Edit task description
  python todo.py priority <id> high      Set task priority
  python todo.py search "query"          Search tasks
  python todo.py help                    Show this help
""")

def main():
    tasks = load_tasks()
    args  = sys.argv[1:]

    if not args:
        interactive_menu(tasks)
        return

    cmd = args[0].lower()

    if cmd == "add":
        if len(args) < 2:
            print(error("  Usage: python todo.py add \"Description\" [priority] [YYYY-MM-DD]"))
            return
        desc     = args[1]
        priority = args[2] if len(args) > 2 else "medium"
        due_date = args[3] if len(args) > 3 else None
        add_task(tasks, desc, priority, due_date)

    elif cmd in ("list", "ls"):
        filter_by = args[1].lower() if len(args) > 1 else "all"
        print_tasks(tasks, filter_by)

    elif cmd in ("complete", "done", "check"):
        if len(args) < 2 or not args[1].isdigit():
            print(error("  Usage: python todo.py complete <id>"))
            return
        complete_task(tasks, int(args[1]))

    elif cmd in ("delete", "del", "remove", "rm"):
        if len(args) < 2 or not args[1].isdigit():
            print(error("  Usage: python todo.py delete <id>"))
            return
        delete_task(tasks, int(args[1]))

    elif cmd == "edit":
        if len(args) < 3 or not args[1].isdigit():
            print(error("  Usage: python todo.py edit <id> \"New description\""))
            return
        edit_task(tasks, int(args[1]), args[2])

    elif cmd == "priority":
        if len(args) < 3 or not args[1].isdigit():
            print(error("  Usage: python todo.py priority <id> <low|medium|high>"))
            return
        set_priority(tasks, int(args[1]), args[2])

    elif cmd == "search":
        if len(args) < 2:
            print(error("  Usage: python todo.py search \"query\""))
            return
        search_tasks(tasks, args[1])

    elif cmd in ("help", "--help", "-h"):
        print_help()

    else:
        print(warn(f"  Unknown command '{cmd}'. Run 'python todo.py help' for usage."))

if __name__ == "__main__":
    main()
