# Python 桌面待办事项工具

一个基于 **Tkinter** 的桌面待办工具，界面为深色卡片风格，支持任务分类、筛选和到期提醒。

## 功能

- 新增 / 编辑 / 删除任务
- 自定义任务分类
- 按分类和完成状态筛选
- 支持截止时间（`YYYY-MM-DD HH:MM`）
- 到期前提醒弹窗（每 30 秒检查一次）
- 本地 JSON 持久化存储

## 运行方式

```bash
python3 app.py
```

## 打包为 Windows 双击运行的 `.exe`（PyInstaller）

### 方式一：一键脚本（推荐）

在 Windows 的命令提示符中进入项目目录，双击或运行：

```bat
build_exe.bat
```

打包完成后，生成文件在：

```text
dist\TodoDesktop.exe
```

双击 `TodoDesktop.exe` 即可直接运行。

### 方式二：手动命令

```bash
py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --clean --windowed --onefile --name TodoDesktop app.py
```

## 说明

- 打包后程序的数据文件 `todo_data.json` 会写在 EXE 同目录下，便于携带和备份。
- 如果你在公司电脑上无法执行，可能需要对 EXE 做代码签名或加白名单。

## 数据文件

程序会在当前目录自动生成：

- `todo_data.json`：保存任务与分类数据
