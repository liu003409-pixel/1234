const STORAGE_KEY = "simple-reminders-v1";
const form = document.getElementById("reminder-form");
const titleInput = document.getElementById("title");
const timeInput = document.getElementById("time");
const listEl = document.getElementById("reminder-list");
const emptyStateEl = document.getElementById("empty-state");
const clearAllBtn = document.getElementById("clear-all");

/** @type {{id:string,title:string,time:string,done:boolean,notified:boolean}[]} */
let reminders = [];

const uid = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

function loadReminders() {
  try {
    reminders = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    if (!Array.isArray(reminders)) reminders = [];
  } catch {
    reminders = [];
  }
}

function saveReminders() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reminders));
}

function formatTime(isoString) {
  return new Date(isoString).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function render() {
  reminders.sort((a, b) => new Date(a.time) - new Date(b.time));
  listEl.innerHTML = "";

  reminders.forEach((item) => {
    const li = document.createElement("li");
    li.className = `item ${item.done ? "done" : ""}`;

    const info = document.createElement("div");
    info.innerHTML = `<div class="item-title">${item.title}</div><div class="item-time">${formatTime(item.time)}</div>`;

    const actions = document.createElement("div");
    actions.className = "item-actions";

    const toggleBtn = document.createElement("button");
    toggleBtn.className = "secondary";
    toggleBtn.textContent = item.done ? "恢复" : "完成";
    toggleBtn.onclick = () => {
      item.done = !item.done;
      saveReminders();
      render();
    };

    const removeBtn = document.createElement("button");
    removeBtn.className = "danger";
    removeBtn.textContent = "删除";
    removeBtn.onclick = () => {
      reminders = reminders.filter((r) => r.id !== item.id);
      saveReminders();
      render();
    };

    actions.append(toggleBtn, removeBtn);
    li.append(info, actions);
    listEl.appendChild(li);
  });

  emptyStateEl.style.display = reminders.length ? "none" : "block";
}

async function requestNotificationPermission() {
  if (!("Notification" in window)) return;
  if (Notification.permission === "default") {
    await Notification.requestPermission();
  }
}

function checkDueReminders() {
  const now = Date.now();
  reminders.forEach((item) => {
    if (item.done || item.notified) return;

    const due = new Date(item.time).getTime();
    if (due <= now) {
      item.notified = true;
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("日程提醒", { body: item.title });
      } else {
        alert(`提醒：${item.title}`);
      }
    }
  });
  saveReminders();
  render();
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const title = titleInput.value.trim();
  const time = timeInput.value;
  if (!title || !time) return;

  if (new Date(time).getTime() < Date.now()) {
    alert("提醒时间不能早于当前时间");
    return;
  }

  reminders.push({ id: uid(), title, time, done: false, notified: false });
  saveReminders();
  render();

  form.reset();
  await requestNotificationPermission();
});

clearAllBtn.addEventListener("click", () => {
  if (!reminders.length) return;
  if (confirm("确定要清空所有提醒吗？")) {
    reminders = [];
    saveReminders();
    render();
  }
});

loadReminders();
render();
requestNotificationPermission();
setInterval(checkDueReminders, 1000);
