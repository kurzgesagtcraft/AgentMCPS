#!/usr/bin/env python3
"""
Cradle GUI MCP Server (Saxifei Edition)
基于 ComputerAgent (Cradle) 架构深度重构的视觉代理核心
支持动态技能注册、精确 IO 追踪、多维窗口管理以及 SAM/GroundingDINO 视觉感知
"""
import json
import base64
import time
import asyncio
import io
import platform
import threading
import inspect
import re
import ast
import subprocess
import os
import gc
import glob
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union, Callable
from dataclasses import dataclass, field

import mss
import mss.tools
import pyautogui
import pydirectinput
import numpy as np
import torch

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, ImageContent
except ImportError:
    print("请安装 MCP SDK: pip install mcp")
    exit(1)

# 视觉组件加载 (可选)
HAS_VISION = False
try:
    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor
    HAS_VISION = True
except ImportError:
    print("[CradleGUI] Vision components (segment-anything) not found. Vision tools will be limited.")

class IOEnvironment:
    """
    单例模式的 IO 环境管理器
    负责底层操作执行与状态追踪
    """
    _instance = None
    _lock = threading.Lock()

    # 别名定义
    ALIASES_RIGHT_MOUSE = ['right', 'rightbutton', 'rightmousebutton', 'r', 'rbutton', 'rmouse', 'rightmouse', 'rm', 'mouseright']
    ALIASES_LEFT_MOUSE = ['left', 'leftbutton', 'leftmousebutton', 'l', 'lbutton', 'lmouse', 'leftmouse', 'lm', 'mouseleft']
    ALIASES_MIDDLE_MOUSE = ['middle', 'middlebutton', 'middlemousebutton', 'm', 'mbutton', 'mmouse', 'middlemouse', 'center', 'c']
    
    ALIASES_SHIFT = ['shift', 'lshift', 'rshift', 'leftshift', 'rightshift']
    ALIASES_CTRL = ['ctrl', 'control', 'rctrl', 'lctrl', 'rightcontrol', 'leftcontrol']
    ALIASES_ALT = ['alt', 'option', 'lalt', 'ralt', 'leftalt', 'rightalt']
    ALIASES_WIN = ['win', 'command', 'meta', 'super', 'lwin', 'rwin']

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.screen_width, self.screen_height = pyautogui.size()
        self.held_keys = set()
        self.held_buttons = set()
        
        # 基础配置
        pyautogui.FAILSAFE = False
        if platform.system() == "Windows":
            pydirectinput.FAILSAFE = False
            
        # 视觉模型初始化
        self.sam_model = None
        self.mask_generator = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"[CradleGUI] IO System Ready: {self.screen_width}x{self.screen_height} on {self.device}")

    def init_vision(self, model_type="vit_h", checkpoint_path="./cache/sam_vit_h_4b8939.pth"):
        if not HAS_VISION:
            return "Vision components not installed."
        try:
            if not os.path.exists(checkpoint_path):
                return f"Checkpoint not found at {checkpoint_path}"
            
            self.sam_model = sam_model_registry[model_type](checkpoint=checkpoint_path).to(self.device)
            self.mask_generator = SamAutomaticMaskGenerator(self.sam_model)
            return f"SAM ({model_type}) initialized on {self.device}"
        except Exception as e:
            return f"Failed to init vision: {str(e)}"

    def map_button(self, button: str) -> str:
        btn = button.lower().strip()
        if btn in self.ALIASES_LEFT_MOUSE: return 'left'
        if btn in self.ALIASES_RIGHT_MOUSE: return 'right'
        if btn in self.ALIASES_MIDDLE_MOUSE: return 'middle'
        return btn

    def map_key(self, key: str) -> str:
        k = key.lower().strip()
        if k in self.ALIASES_SHIFT: return 'shift'
        if k in self.ALIASES_CTRL: return 'ctrl'
        if k in self.ALIASES_ALT: return 'alt'
        if k in self.ALIASES_WIN: return 'win'
        return k

    def normalize_to_real(self, x: float, y: float) -> Tuple[int, int]:
        """归一化坐标 (0-1000) -> 像素坐标"""
        rx = int((x / 1000.0) * self.screen_width)
        ry = int((y / 1000.0) * self.screen_height)
        return rx, ry

    def capture_screen(self, scale: float = 0.8, max_dim: int = 1280, show_grid: bool = False, show_cursor: bool = False, save_path: Optional[str] = None) -> Dict[str, Any]:
        """全屏截图，支持缩放、长边限制、网格叠加、光标绘制与持久化保存"""
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                # 参考 ComputerAgent 使用 bgra 模式以确保兼容性
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                draw = ImageDraw.Draw(img)
            w, h = img.size

            # 叠加网格 (在缩放前绘制以保证精度)
            if show_grid:
                # 绘制 10x10 网格
                for i in range(1, 10):
                    x = int(w * i / 10)
                    y = int(h * i / 10)
                    draw.line([(x, 0), (x, h)], fill=(255, 0, 0, 128), width=1)
                    draw.line([(0, y), (w, y)], fill=(255, 0, 0, 128), width=1)
                    draw.text((x + 2, 2), str(i*100), fill="red")
                    draw.text((2, y + 2), str(i*100), fill="red")

            # 绘制光标 (参考 ComputerAgent 增强感知)
            if show_cursor:
                px, py = pyautogui.position()
                # 绘制十字准星
                draw.line([(px - 20, py), (px + 20, py)], fill="blue", width=2)
                draw.line([(px, py - 20), (px, py + 20)], fill="blue", width=2)
                draw.ellipse([px - 5, py - 5, px + 5, py + 5], outline="blue", width=2)
                draw.text((px + 10, py + 10), f"({px},{py})", fill="blue")

            # 计算缩放比例，确保长边不超过 max_dim
            current_max = max(img.width, img.height)
            if current_max * scale > max_dim:
                scale = max_dim / current_max
                
            if scale < 1.0:
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.LANCZOS)
            
            # 持久化保存
            if save_path:
                p = Path(save_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                img.save(str(p), format="JPEG", quality=80)

            buffered = io.BytesIO()
            # 质量稍微回升到 50，平衡清晰度与体积
            img.save(buffered, format="JPEG", quality=50, optimize=True)
            img_data = buffered.getvalue()
            
            return {
                "image": base64.b64encode(img_data).decode("utf-8"),
                "width": img.width,
                "height": img.height,
                "format": "jpeg",
                "scale": scale,
                "saved_to": save_path
            }
        except Exception as e:
            return {"error": f"Capture failed: {str(e)}"}

    def get_som(self, scale: float = 0.5) -> Dict[str, Any]:
        """获取带有视觉标记 (Set-of-Mark) 的截图，优化体积"""
        if self.mask_generator is None:
            return {"error": "SAM model not initialized. Call init_vision first."}
        
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # 缩放以加速处理并作为最终输出基础
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
            img_np = np.array(img)
            
            masks = self.mask_generator.generate(img_np)
            
            # 在缩放后的图上绘制标记
            draw = ImageDraw.Draw(img)
            som_map = {}
            
            # 过滤并排序 mask
            masks = sorted(masks, key=lambda x: x['area'], reverse=True)
            
            count = 0
            for i, mask in enumerate(masks):
                # 过滤太小或太大的 mask
                if mask['area'] < 50 or mask['area'] > (img_np.shape[0] * img_np.shape[1] * 0.8):
                    continue
                
                count += 1
                rx, ry, rw, rh = mask['bbox'] # [x, y, w, h] in current scaled coords
                
                # 绘制边框
                draw.rectangle([rx, ry, rx + rw, ry + rh], outline="red", width=1)
                
                # 绘制编号
                label = str(count)
                draw.text((rx + 2, ry + 2), label, fill="yellow")
                
                # 记录中心点 (归一化到 0-1000)
                cx = (rx + rw/2) / img.width * 1000
                cy = (ry + rh/2) / img.height * 1000
                som_map[label] = {"x": cx, "y": cy, "bbox": [rx, ry, rw, rh]}
                
                if count >= 80: break # 稍微增加标记上限到 80
            
            buffered = io.BytesIO()
            # 质量回升到 40
            img.save(buffered, format="JPEG", quality=40, optimize=True)
            img_data = buffered.getvalue()
            
            return {
                "image": base64.b64encode(img_data).decode("utf-8"),
                "som_map": som_map,
                "count": count
            }
        except Exception as e:
            return {"error": f"SOM failed: {str(e)}"}

    # --- 鼠标核心 ---
    def mouse_move(self, x: float, y: float, duration: float = 0.1):
        rx, ry = self.normalize_to_real(x, y)
        pyautogui.moveTo(rx, ry, duration=duration)
        return f"Mouse moved to ({rx}, {ry})"

    def mouse_click(self, x: float, y: float, button: str = 'left', clicks: int = 1):
        rx, ry = self.normalize_to_real(x, y)
        btn = self.map_button(button)
        pyautogui.click(x=rx, y=ry, clicks=clicks, button=btn)
        return f"Clicked {btn} at ({rx}, {ry}) x{clicks}"

    def mouse_drag(self, x1: float, y1: float, x2: float, y2: float, button: str = 'left'):
        rx1, ry1 = self.normalize_to_real(x1, y1)
        rx2, ry2 = self.normalize_to_real(x2, y2)
        btn = self.map_button(button)
        pyautogui.moveTo(rx1, ry1)
        pyautogui.dragTo(rx2, ry2, button=btn, duration=0.5)
        return f"Dragged {btn} from ({rx1}, {ry1}) to ({rx2}, {ry2})"

    def mouse_down(self, button: str = 'left'):
        btn = self.map_button(button)
        pyautogui.mouseDown(button=btn)
        self.held_buttons.add(btn)
        return f"Mouse {btn} down"

    def mouse_up(self, button: str = 'left'):
        btn = self.map_button(button)
        pyautogui.mouseUp(button=btn)
        if btn in self.held_buttons:
            self.held_buttons.remove(btn)
        return f"Mouse {btn} up"

    def mouse_scroll(self, amount: int):
        pyautogui.scroll(amount)
        return f"Scrolled {amount}"

    # --- 键盘核心 ---
    def key_down(self, key: str):
        k = self.map_key(key)
        if platform.system() == "Windows":
            pydirectinput.keyDown(k)
        else:
            pyautogui.keyDown(k)
        self.held_keys.add(k)
        return f"Key {k} down"

    def key_up(self, key: str):
        k = self.map_key(key)
        if platform.system() == "Windows":
            pydirectinput.keyUp(k)
        else:
            pyautogui.keyUp(k)
        if k in self.held_keys:
            self.held_keys.remove(k)
        return f"Key {k} up"

    def key_press(self, key: str, presses: int = 1):
        k = self.map_key(key)
        if platform.system() == "Windows":
            pydirectinput.press(k, presses=presses)
        else:
            pyautogui.press(k, presses=presses)
        return f"Pressed key {k} {presses} times"

    def hotkey(self, keys: List[str]):
        ks = [self.map_key(k) for k in keys]
        pyautogui.hotkey(*ks)
        return f"Executed hotkey: {'+'.join(ks)}"

    def type_text(self, text: str):
        pyautogui.write(text, interval=0.02)
        return f"Typed: {text}"

    def release_all(self):
        for key in list(self.held_keys):
            k = self.map_key(key)
            if platform.system() == "Windows":
                pydirectinput.keyUp(k)
            else:
                pyautogui.keyUp(k)
        self.held_keys.clear()
        for btn in list(self.held_buttons):
            b = self.map_button(btn)
            pyautogui.mouseUp(button=b)
        self.held_buttons.clear()
        return "All IO released"

    def get_mouse_position(self) -> Dict[str, float]:
        """获取当前鼠标的归一化坐标"""
        px, py = pyautogui.position()
        return {
            "x": (px / self.screen_width) * 1000.0,
            "y": (py / self.screen_height) * 1000.0,
            "real_x": px,
            "real_y": py
        }

    def launch_app(self, command: str):
        """启动应用程序"""
        try:
            subprocess.Popen(command, shell=True)
            return f"App launched with command: {command}"
        except Exception as e:
            return f"Failed to launch app: {str(e)}"

@dataclass
class Skill:
    name: str
    func: Callable
    description: str
    parameters: Dict[str, str]
    code: str = ""

class SkillRegistry:
    """
    技能注册表
    支持从代码动态注册新技能，并持久化存储
    """
    def __init__(self, io: IOEnvironment):
        self.io = io
        self.skills: Dict[str, Skill] = {}
        self.persistence_path = Path(__file__).parent / "skills_db.json"
        self._init_builtin_skills()
        self._load_persisted_skills()

    def _init_builtin_skills(self):
        self.register_builtin(
            "open_start_menu",
            lambda: self.io.key_press("win"),
            "打开 Windows 开始菜单",
            {}
        )
        self.register_builtin(
            "switch_app",
            lambda: pyautogui.hotkey("alt", "tab"),
            "切换最近使用的应用程序",
            {}
        )

    def register_builtin(self, name, func, desc, params):
        self.skills[name] = Skill(name, func, desc, params)

    def register_from_code(self, code: str) -> str:
        try:
            tree = ast.parse(code)
            func_def = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            func_name = func_def.name
            
            import os, sys
            local_vars = {
                "io": self.io,
                "pyautogui": pyautogui,
                "time": time,
                "os": os,
                "sys": sys,
                "json": json,
                "pydirectinput": pydirectinput,
                "subprocess": subprocess,
                "np": np,
                "torch": torch
            }
            exec(code, globals(), local_vars)
            func_obj = local_vars[func_name]
            
            doc = inspect.getdoc(func_obj) or "无描述"
            sig = inspect.signature(func_obj)
            params = {k: str(v.annotation) for k, v in sig.parameters.items()}
            
            self.skills[func_name] = Skill(func_name, func_obj, doc, params, code)
            self._persist_skills()
            return f"Successfully registered skill: {func_name}"
        except Exception as e:
            return f"Failed to register skill: {str(e)}"

    def _persist_skills(self):
        data = {
            name: {
                "description": s.description,
                "parameters": s.parameters,
                "code": s.code
            }
            for name, s in self.skills.items() if s.code
        }
        with open(self.persistence_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_persisted_skills(self):
        if not self.persistence_path.exists():
            return
        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for name, info in data.items():
                self.register_from_code(info["code"])
        except Exception as e:
            print(f"Error loading persisted skills: {e}")

    def execute(self, name: str, params: Dict[str, Any]) -> str:
        if name not in self.skills:
            return f"Skill {name} not found"
        try:
            res = self.skills[name].func(**params)
            return str(res) if res is not None else f"Executed {name}"
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    def get_skill_code(self, name: str) -> str:
        if name in self.skills:
            return self.skills[name].code or "# Built-in skill (no source code available)"
        return f"Skill {name} not found"

    def delete_skill(self, name: str) -> str:
        if name in self.skills:
            del self.skills[name]
            self._persist_skills()
            return f"Skill {name} deleted"
        return f"Skill {name} not found"

# --- MCP Server ---
app = Server("cradle-gui-mcp")
io_env = IOEnvironment()
registry = SkillRegistry(io_env)

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(name="init_vision", description="初始化视觉模型 (SAM)。",
             inputSchema={
                 "type": "object",
                 "properties": {
                     "model_type": {"type": "string", "default": "vit_h"},
                     "checkpoint_path": {"type": "string", "default": "./cache/sam_vit_h_4b8939.pth"}
                 }
             }),
        Tool(name="get_som", description="获取带有视觉标记 (Set-of-Mark) 的截图和坐标映射。",
             inputSchema={
                 "type": "object",
                 "properties": {
                     "scale": {"type": "number", "default": 0.4}
                 }
             }),
        Tool(name="capture_screen", description="获取全屏截图 (Base64 JPEG)。支持网格叠加、光标绘制与保存。",
             inputSchema={
                 "type": "object",
                 "properties": {
                     "scale": {"type": "number", "default": 0.8},
                     "max_dim": {"type": "integer", "default": 1280},
                     "show_grid": {"type": "boolean", "default": False},
                     "show_cursor": {"type": "boolean", "default": False},
                     "save_path": {"type": "string", "description": "可选的保存路径，例如 'saxifei/current_screen.jpg'"}
                 }
             }),
        Tool(name="mouse_click", description="点击归一化坐标 (0-1000)。", 
             inputSchema={"type": "object", "properties": {
                 "x": {"type": "number"}, "y": {"type": "number"},
                 "button": {"type": "string", "default": "left"},
                 "clicks": {"type": "integer", "default": 1}
             }, "required": ["x", "y"]}),
        Tool(name="mouse_move", description="移动鼠标。", 
             inputSchema={"type": "object", "properties": {
                 "x": {"type": "number"}, "y": {"type": "number"}
             }, "required": ["x", "y"]}),
        Tool(name="type_text", description="输入文本。", 
             inputSchema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}),
        Tool(name="key_press", description="按键。", 
             inputSchema={"type": "object", "properties": {
                 "key": {"type": "string"},
                 "presses": {"type": "integer", "default": 1}
             }, "required": ["key"]}),
        Tool(name="hotkey", description="组合键。",
             inputSchema={"type": "object", "properties": {"keys": {"type": "array", "items": {"type": "string"}}}, "required": ["keys"]}),
        Tool(name="mouse_drag", description="从起点拖拽到终点。",
             inputSchema={"type": "object", "properties": {
                 "x1": {"type": "number"}, "y1": {"type": "number"},
                 "x2": {"type": "number"}, "y2": {"type": "number"},
                 "button": {"type": "string", "default": "left"}
             }, "required": ["x1", "y1", "x2", "y2"]}),
        Tool(name="mouse_scroll", description="滚动滚轮。",
             inputSchema={"type": "object", "properties": {"amount": {"type": "integer"}}, "required": ["amount"]}),
        Tool(name="register_skill", description="动态注册新技能。",
             inputSchema={"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}),
        Tool(name="execute_skill", description="执行已注册的技能。",
             inputSchema={"type": "object", "properties": {
                 "name": {"type": "string"}, "params": {"type": "object", "default": {}}
             }, "required": ["name"]}),
        Tool(name="list_skills", description="列出所有技能。", inputSchema={"type": "object"}),
        Tool(name="get_active_window", description="获取当前活动窗口信息。", inputSchema={"type": "object"}),
        Tool(name="get_window_info", description="获取所有可见窗口列表。", inputSchema={"type": "object"}),
        Tool(name="get_mouse_position", description="获取当前鼠标归一化坐标。", inputSchema={"type": "object"}),
        Tool(name="release_all", description="释放所有按键。", inputSchema={"type": "object"})
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    try:
        if name == "init_vision":
            return [TextContent(type="text", text=io_env.init_vision(arguments.get("model_type", "vit_h"), arguments.get("checkpoint_path", "./cache/sam_vit_h_4b8939.pth")))]
        elif name == "get_som":
            res = io_env.get_som(arguments.get("scale", 0.5))
            if "error" in res:
                return [TextContent(type="text", text=res["error"])]
            return [
                ImageContent(type="image", data=res["image"], mimeType="image/jpeg"),
                TextContent(type="text", text=json.dumps({"som_map": res["som_map"], "count": res["count"]}, ensure_ascii=False))
            ]
        elif name == "capture_screen":
            res = io_env.capture_screen(
                arguments.get("scale", 0.8),
                arguments.get("max_dim", 1280),
                arguments.get("show_grid", False),
                arguments.get("show_cursor", False),
                arguments.get("save_path")
            )
            return [
                ImageContent(type="image", data=res["image"], mimeType="image/jpeg")
            ]
        elif name == "mouse_click":
            return [TextContent(type="text", text=io_env.mouse_click(arguments["x"], arguments["y"], arguments.get("button", "left"), arguments.get("clicks", 1)))]
        elif name == "mouse_move":
            return [TextContent(type="text", text=io_env.mouse_move(arguments["x"], arguments["y"]))]
        elif name == "type_text":
            return [TextContent(type="text", text=io_env.type_text(arguments["text"]))]
        elif name == "key_press":
            return [TextContent(type="text", text=io_env.key_press(arguments["key"], arguments.get("presses", 1)))]
        elif name == "hotkey":
            return [TextContent(type="text", text=io_env.hotkey(arguments["keys"]))]
        elif name == "mouse_drag":
            return [TextContent(type="text", text=io_env.mouse_drag(arguments["x1"], arguments["y1"], arguments["x2"], arguments["y2"], arguments.get("button", "left")))]
        elif name == "mouse_scroll":
            return [TextContent(type="text", text=io_env.mouse_scroll(arguments["amount"]))]
        elif name == "register_skill":
            return [TextContent(type="text", text=registry.register_from_code(arguments["code"]))]
        elif name == "execute_skill":
            return [TextContent(type="text", text=registry.execute(arguments["name"], arguments.get("params", {})))]
        elif name == "list_skills":
            skills = {n: {"desc": s.description, "params": s.parameters} for n, s in registry.skills.items()}
            return [TextContent(type="text", text=json.dumps(skills, ensure_ascii=False))]
        elif name == "get_active_window":
            w = pyautogui.getActiveWindow()
            if w:
                info = {"title": w.title, "rect": [w.left, w.top, w.width, w.height]}
                return [TextContent(type="text", text=json.dumps(info, ensure_ascii=False))]
            return [TextContent(type="text", text="No active window found")]
        elif name == "get_window_info":
            wins = [{"title": w.title, "rect": [w.left, w.top, w.width, w.height]} for w in pyautogui.getAllWindows() if w.title]
            return [TextContent(type="text", text=json.dumps(wins, ensure_ascii=False))]
        elif name == "get_mouse_position":
            return [TextContent(type="text", text=json.dumps(io_env.get_mouse_position()))]
        elif name == "release_all":
            return [TextContent(type="text", text=io_env.release_all())]
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())