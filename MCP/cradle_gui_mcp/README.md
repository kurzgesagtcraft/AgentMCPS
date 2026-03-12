# Cradle GUI MCP Server (Saxifei Edition)

基于 Microsoft ComputerAgent (Cradle) 架构重构的视觉代理核心。

## 特性

- **视觉感知**：通过 `capture_screen` 获取全屏截图，支持多模态模型分析。
- **归一化坐标**：使用 0-1000 的归一化坐标系统，适配任何屏幕分辨率。
- **IO 追踪**：精确追踪按键和鼠标状态，支持 `release_all` 紧急释放。
- **动态技能系统**：支持通过 Python 代码动态注册新技能，并自动持久化到 `skills_db.json`。
- **窗口管理**：支持获取所有窗口信息及切换窗口。

## 安装

1. 运行 `install.bat` 创建虚拟环境并安装依赖。
2. 在 MCP 配置文件中添加以下配置：

```json
{
  "mcpServers": {
    "cradle-gui": {
      "command": "d:/vscode/VCPToolBox/MCP/cradle_gui_mcp/.venv/Scripts/python.exe",
      "args": ["-m", "server"],
      "cwd": "d:/vscode/VCPToolBox/MCP/cradle_gui_mcp"
    }
  }
}
```

## 工具列表

- `capture_screen`: 获取全屏截图。
- `mouse_click`: 点击坐标。
- `mouse_move`: 移动鼠标。
- `mouse_drag`: 拖拽。
- `type_text`: 输入文本。
- `key_press`: 按键。
- `hotkey`: 组合键。
- `register_skill`: 动态注册技能。
- `execute_skill`: 执行技能。
- `list_skills`: 列出技能。
- `get_window_info`: 获取窗口列表。
- `release_all`: 释放所有 IO。