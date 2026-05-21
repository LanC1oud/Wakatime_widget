# WakaTime 桌面组件

一个轻量级的 Windows 桌面悬浮小组件，实时展示 WakaTime 编码统计，支持历史语言排行榜与今日时长切换。

## 功能

- **语言排行榜** — 水平彩色条形图展示各语言时长占比
- **时间范围切换** — 今日 / 最近7天 / 最近30天 / 最近6个月 / 全部时间
- **展开收起** — 点击 ▲/▼ 切换完整模式与极简模式（仅显示总时长）
- **置顶悬浮** — 窗口始终置顶，无边框设计，支持任意位置拖动
- **自动刷新** — 每 2 分钟自动拉取最新数据

## 文件说明

| 文件 | 说明 |
|------|------|
| `wakatime_widget.py` | 组件主程序 |
| `启动WakaTime组件.bat` | 一键启动脚本（自动检查依赖） |

## 使用方式

### 1. 前置条件

- 已安装 **Python 3**（[下载地址](https://www.python.org/downloads/)）
- 已安装并配置好 **WakaTime**（拥有 `~/.wakatime.cfg`）

### 2. 启动

双击桌面上的 `启动WakaTime组件.bat` 即可运行。

如果缺少 `requests` 库，脚本会自动安装：

```bash
pip install requests
```

### 3. 手动运行

```bash
python wakatime_widget.py
```

## 界面操作

| 操作 | 说明 |
|------|------|
| 拖动窗口 | 按住鼠标左键拖动任意空白区域 |
| 切换时间范围 | 点击标题栏 **"最近7天 ▾"** 展开下拉菜单选择 |
| 展开/收起 | 点击 ▲ 收起为极简模式，点击 ▼ 展开完整排行榜 |
| 关闭 | 点击右上角 **×** |

## 配置

组件会自动读取 `C:\Users\<用户名>\.wakatime.cfg` 中的 API Key，无需手动填写。

配置文件示例：

```ini
[settings]
api_key = waka_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## 自定义样式

编辑 `wakatime_widget.py` 顶部的配置区即可修改配色：

```python
BG_COLOR = "#1e1e2e"        # 背景色
ACCENT_COLOR = "#89b4fa"    # 主色调（总时长文字）
SECONDARY_FG = "#6c7086"    # 次要文字色
BAR_BG = "#313244"          # 进度条背景色
```

语言颜色映射在 `LANG_COLORS` 字典中按需增删。

## 开机自启

将 `启动WakaTime组件.bat` 放入以下目录即可开机自动运行：

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

## 常见问题

**Q: 窗口打不开或报错？**  
检查 `~/.wakatime.cfg` 是否存在且包含有效的 `api_key`。

**Q: 数据一直显示 "--"？**  
确认今天有编码记录。如果是首次使用 WakaTime，插件可能需要几分钟同步数据。

**Q: 语言颜色不够全？**  
在 `LANG_COLORS` 字典中添加对应语言与十六进制颜色值即可。

## 依赖

- Python >= 3.7
- requests
- tkinter（Windows 默认自带）
