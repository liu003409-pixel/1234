import json
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

DATE_FMT = "%Y-%m-%d %H:%M"


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


DATA_FILE = get_app_dir() / "todo_data.json"


@dataclass
class Task:
    id: str
    title: str
    category: str
    due_at: str
    notes: str
    completed: bool = False
    reminded: bool = False


class TodoApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("✨ 美观待办事项工具")
        self.root.geometry("980x620")
        self.root.minsize(900, 560)

        self.tasks: list[Task] = []
        self.categories = ["工作", "学习", "生活", "健康"]

        self._configure_style()
        self._build_ui()
        self._load_data()
        self.refresh_list()

        self._schedule_reminder_check()

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        bg = "#101826"
        card = "#182337"
        text = "#E6ECF5"
        accent = "#7AA2F7"
        muted = "#97A3B6"

        self.root.configure(bg=bg)

        style.configure("App.TFrame", background=bg)
        style.configure("Card.TFrame", background=card)
        style.configure("TLabel", background=card, foreground=text, font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel", background=card, foreground=text, font=("Microsoft YaHei UI", 14, "bold"))
        style.configure("Muted.TLabel", background=card, foreground=muted, font=("Microsoft YaHei UI", 9))

        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(10, 7), borderwidth=0)
        style.map("TButton", background=[("active", "#5E88F2")], foreground=[("active", "#FFFFFF")])
        style.configure("Accent.TButton", background=accent, foreground="#FFFFFF")
        style.map("Accent.TButton", background=[("active", "#5E88F2")])

        style.configure(
            "Treeview",
            background="#0F172A",
            fieldbackground="#0F172A",
            foreground="#E2E8F0",
            rowheight=30,
            bordercolor=card,
            borderwidth=0,
            font=("Microsoft YaHei UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#1E293B",
            foreground="#E2E8F0",
            relief="flat",
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", "#334155")])

        style.configure("TEntry", fieldbackground="#F8FAFC", padding=6)
        style.configure("TCombobox", fieldbackground="#F8FAFC", padding=5)

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, style="App.TFrame", padding=14)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, style="Card.TFrame", padding=16)
        left.pack(side="left", fill="y", padx=(0, 12))

        right = ttk.Frame(main, style="Card.TFrame", padding=16)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="添加 / 编辑任务", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left, text="支持分类、截止时间和提醒", style="Muted.TLabel").pack(anchor="w", pady=(2, 16))

        self.title_var = tk.StringVar()
        self.category_var = tk.StringVar(value=self.categories[0])
        self.due_var = tk.StringVar(value=(datetime.now() + timedelta(hours=1)).strftime(DATE_FMT))
        self.filter_category_var = tk.StringVar(value="全部")
        self.filter_status_var = tk.StringVar(value="全部")

        self.task_id_editing: str | None = None

        self._field(left, "任务标题", ttk.Entry(left, textvariable=self.title_var, width=32))

        self.category_combo = ttk.Combobox(left, textvariable=self.category_var, values=self.categories, state="normal", width=29)
        self._field(left, "分类", self.category_combo)

        self._field(left, f"截止时间（格式：{DATE_FMT}）", ttk.Entry(left, textvariable=self.due_var, width=32))

        ttk.Label(left, text="备注", style="TLabel").pack(anchor="w", pady=(6, 4))
        self.notes_text = tk.Text(left, height=8, width=34, bg="#F8FAFC", fg="#0F172A", relief="flat", padx=8, pady=8)
        self.notes_text.pack(fill="x")

        btn_row = ttk.Frame(left, style="Card.TFrame")
        btn_row.pack(fill="x", pady=(12, 0))
        ttk.Button(btn_row, text="保存任务", style="Accent.TButton", command=self.save_task).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="清空", command=self.clear_form).pack(side="left")

        ttk.Separator(left).pack(fill="x", pady=14)
        ttk.Label(left, text="筛选", style="Title.TLabel").pack(anchor="w", pady=(0, 8))

        self.filter_category_combo = ttk.Combobox(left, textvariable=self.filter_category_var, values=["全部", *self.categories], state="readonly", width=29)
        self._field(left, "分类筛选", self.filter_category_combo)

        self.filter_status_combo = ttk.Combobox(left, textvariable=self.filter_status_var, values=["全部", "未完成", "已完成"], state="readonly", width=29)
        self._field(left, "状态筛选", self.filter_status_combo)

        ttk.Button(left, text="应用筛选", command=self.refresh_list).pack(anchor="w", pady=(8, 0))

        header = ttk.Frame(right, style="Card.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="任务列表", style="Title.TLabel").pack(side="left")

        actions = ttk.Frame(header, style="Card.TFrame")
        actions.pack(side="right")
        ttk.Button(actions, text="标记完成", command=self.mark_done).pack(side="left", padx=4)
        ttk.Button(actions, text="编辑", command=self.load_selected_for_edit).pack(side="left", padx=4)
        ttk.Button(actions, text="删除", command=self.delete_selected).pack(side="left", padx=4)

        columns = ("status", "title", "category", "due")
        self.tree = ttk.Treeview(right, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("status", text="状态")
        self.tree.heading("title", text="任务")
        self.tree.heading("category", text="分类")
        self.tree.heading("due", text="截止时间")

        self.tree.column("status", width=90, anchor="center")
        self.tree.column("title", width=350)
        self.tree.column("category", width=120, anchor="center")
        self.tree.column("due", width=170, anchor="center")

        self.tree.pack(fill="both", expand=True, pady=(12, 0))
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_hint())

        self.hint_var = tk.StringVar(value="提示：选择一条任务后可以编辑/删除/标记完成。")
        ttk.Label(right, textvariable=self.hint_var, style="Muted.TLabel").pack(anchor="w", pady=(8, 0))

    @staticmethod
    def _field(parent: ttk.Frame, label: str, widget: ttk.Widget) -> None:
        ttk.Label(parent, text=label, style="TLabel").pack(anchor="w", pady=(6, 4))
        widget.pack(anchor="w", fill="x")

    def _update_hint(self) -> None:
        task = self._get_selected_task()
        if task:
            self.hint_var.set(f"已选择：{task.title}（{task.category}）")

    def save_task(self) -> None:
        title = self.title_var.get().strip()
        category = self.category_var.get().strip() or "未分类"
        due_text = self.due_var.get().strip()
        notes = self.notes_text.get("1.0", "end").strip()

        if not title:
            messagebox.showwarning("提示", "请填写任务标题。")
            return

        try:
            due_dt = datetime.strptime(due_text, DATE_FMT)
        except ValueError:
            messagebox.showerror("格式错误", f"截止时间格式需要是：{DATE_FMT}")
            return

        if category not in self.categories:
            self.categories.append(category)
            self.categories.sort()
            self._sync_category_comboboxes()

        if self.task_id_editing:
            task = next((t for t in self.tasks if t.id == self.task_id_editing), None)
            if task:
                task.title = title
                task.category = category
                task.due_at = due_dt.strftime(DATE_FMT)
                task.notes = notes
                task.reminded = False
        else:
            self.tasks.append(
                Task(
                    id=str(uuid.uuid4()),
                    title=title,
                    category=category,
                    due_at=due_dt.strftime(DATE_FMT),
                    notes=notes,
                )
            )

        self._save_data()
        self.refresh_list()
        self.clear_form()

    def clear_form(self) -> None:
        self.task_id_editing = None
        self.title_var.set("")
        self.category_var.set(self.categories[0] if self.categories else "未分类")
        self.due_var.set((datetime.now() + timedelta(hours=1)).strftime(DATE_FMT))
        self.notes_text.delete("1.0", "end")

    def refresh_list(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtered = self._filtered_tasks()
        filtered.sort(key=lambda t: datetime.strptime(t.due_at, DATE_FMT))

        for task in filtered:
            status = "✅ 完成" if task.completed else "🕒 待办"
            self.tree.insert("", "end", iid=task.id, values=(status, task.title, task.category, task.due_at))

        self._update_hint()

    def _filtered_tasks(self) -> list[Task]:
        category_filter = self.filter_category_var.get()
        status_filter = self.filter_status_var.get()

        result = self.tasks
        if category_filter != "全部":
            result = [t for t in result if t.category == category_filter]

        if status_filter == "未完成":
            result = [t for t in result if not t.completed]
        elif status_filter == "已完成":
            result = [t for t in result if t.completed]

        return result

    def _get_selected_task(self) -> Task | None:
        selected = self.tree.selection()
        if not selected:
            return None
        task_id = selected[0]
        return next((t for t in self.tasks if t.id == task_id), None)

    def load_selected_for_edit(self) -> None:
        task = self._get_selected_task()
        if not task:
            messagebox.showinfo("提示", "请先选择一条任务。")
            return

        self.task_id_editing = task.id
        self.title_var.set(task.title)
        self.category_var.set(task.category)
        self.due_var.set(task.due_at)
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", task.notes)

    def mark_done(self) -> None:
        task = self._get_selected_task()
        if not task:
            messagebox.showinfo("提示", "请先选择一条任务。")
            return

        task.completed = True
        self._save_data()
        self.refresh_list()

    def delete_selected(self) -> None:
        task = self._get_selected_task()
        if not task:
            messagebox.showinfo("提示", "请先选择一条任务。")
            return

        ok = messagebox.askyesno("确认删除", f"确认删除任务：{task.title}？")
        if not ok:
            return

        self.tasks = [t for t in self.tasks if t.id != task.id]
        self._save_data()
        self.refresh_list()

    def _schedule_reminder_check(self) -> None:
        self._check_reminders()
        self.root.after(30_000, self._schedule_reminder_check)

    def _check_reminders(self) -> None:
        now = datetime.now()
        due_window = now + timedelta(minutes=1)

        for task in self.tasks:
            if task.completed or task.reminded:
                continue
            due_time = datetime.strptime(task.due_at, DATE_FMT)
            if now <= due_time <= due_window:
                messagebox.showinfo("任务提醒", f"任务即将到期：{task.title}\n分类：{task.category}\n截止：{task.due_at}")
                task.reminded = True
                self._save_data()

    def _sync_category_comboboxes(self) -> None:
        self.category_combo["values"] = self.categories
        self.filter_category_combo["values"] = ["全部", *self.categories]

    def _load_data(self) -> None:
        if not DATA_FILE.exists():
            return

        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            self.categories = data.get("categories", self.categories)
            self.tasks = [Task(**item) for item in data.get("tasks", [])]
            self._sync_category_comboboxes()
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            messagebox.showwarning("读取失败", f"无法读取本地数据：{exc}")

    def _save_data(self) -> None:
        payload = {
            "categories": self.categories,
            "tasks": [asdict(t) for t in self.tasks],
        }
        DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
