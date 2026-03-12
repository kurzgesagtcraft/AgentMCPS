import os
import sys
import uuid
import json
import time
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List
from PIL import Image
from mcp.server.fastmcp import FastMCP

from utils.controller import AndroidController, HarmonyOSController, WindowsController

# Initialize FastMCP server
mcp = FastMCP("MobileAgent")

# Global task storage
tasks: Dict[str, Dict[str, Any]] = {}

def log_debug(message):
    with open("mobile_agent_debug.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")

@mcp.tool()
def initialize_task(
    instruction: str,
    device_type: str,
    adb_path: Optional[str] = None,
    hdc_path: Optional[str] = None,
    coor_type: str = "abs",
    add_info: str = ""
) -> str:
    """Initialize a new mobile agent task. coor_type can be 'abs' or 'rel' (0-1000)."""
    log_debug(f"Initializing task: {instruction} for {device_type}")
    task_id = str(uuid.uuid4())
    
    try:
        if device_type == "android":
            controller = AndroidController(adb_path)
        elif device_type == "harmonyos":
            controller = HarmonyOSController(hdc_path)
        elif device_type == "windows":
            log_debug("Creating WindowsController...")
            controller = WindowsController()
            log_debug("WindowsController created.")
        else:
            return "Error: Invalid device_type. Must be 'android', 'harmonyos' or 'windows'."
    except Exception as e:
        log_debug(f"Error creating controller: {str(e)}")
        return f"Error creating controller: {str(e)}"

    # Create log directory
    log_dir = os.path.join("logs", f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_id[:8]}")
    os.makedirs(os.path.join(log_dir, "images"), exist_ok=True)

    tasks[task_id] = {
        "instruction": instruction,
        "controller": controller,
        "log_dir": log_dir,
        "step": 0,
        "coor_type": coor_type,
        "add_info": add_info,
        "history": []
    }
    
    log_debug(f"Task {task_id} initialized for {device_type}")
    return f"Task initialized. ID: {task_id}. Instruction: {instruction}"

@mcp.tool()
def get_screenshot(task_id: str) -> Dict[str, Any]:
    """Capture and return the current screen as base64 and file path."""
    if task_id not in tasks:
        return {"error": "Task ID not found."}
    
    task = tasks[task_id]
    controller = task["controller"]
    log_dir = task["log_dir"]
    step = task["step"]

    screenshot_path = os.path.join(log_dir, "images", f"step_{step}_current.png")
    if not controller.get_screenshot(screenshot_path):
        return {"error": "Failed to capture screenshot."}
    
    with open(screenshot_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode('utf-8')
    
    img = Image.open(screenshot_path)
    width, height = img.size

    return {
        "task_id": task_id,
        "step": step,
        "width": width,
        "height": height,
        "screenshot_path": screenshot_path,
        "base64_image": base64_image
    }

@mcp.tool()
def execute_action(
    task_id: str,
    action: str,
    coordinate: Optional[List[int]] = None,
    coordinate2: Optional[List[int]] = None,
    text: Optional[str] = None,
    button: Optional[str] = None
) -> str:
    """Execute a specific action on the device."""
    if task_id not in tasks:
        return "Error: Task ID not found."
    
    task = tasks[task_id]
    controller = task["controller"]
    
    # Get screen dimensions for relative coordinate conversion
    screenshot_path = os.path.join(task["log_dir"], "images", f"temp_dim.png")
    controller.get_screenshot(screenshot_path)
    width, height = Image.open(screenshot_path).size

    if task.get("coor_type") != "abs":
        if coordinate:
            coordinate = [int(coordinate[0] / 1000 * width), int(coordinate[1] / 1000 * height)]
        if coordinate2:
            coordinate2 = [int(coordinate2[0] / 1000 * width), int(coordinate2[1] / 1000 * height)]

    result_msg = f"Action: {action}"

    if action == "click":
        controller.tap(coordinate[0], coordinate[1])
        result_msg += f" at {coordinate}"
    elif action == "swipe":
        controller.slide(coordinate[0], coordinate[1], coordinate2[0], coordinate2[1])
        result_msg += f" from {coordinate} to {coordinate2}"
    elif action == "type":
        controller.type(text)
        result_msg += f" text: {text}"
    elif action == "system_button":
        if button == "Back": controller.back()
        elif button == "Home": controller.home()
        result_msg += f" button: {button}"
    else:
        return f"Error: Unsupported action {action}"

    task["history"].append({
        "step": task["step"],
        "action": action,
        "params": {"coordinate": coordinate, "coordinate2": coordinate2, "text": text, "button": button},
        "timestamp": datetime.now().isoformat()
    })
    
    task["step"] += 1
    time.sleep(2)
    return f"Action executed: {result_msg}"

@mcp.tool()
def get_task_status(task_id: str) -> str:
    """Get the current status and history of a task."""
    if task_id not in tasks:
        return "Error: Task ID not found."
    
    task = tasks[task_id]
    status = {
        "instruction": task["instruction"],
        "step": task["step"],
        "history": task["history"],
        "add_info": task["add_info"]
    }
    return json.dumps(status, indent=2)

@mcp.tool()
def stop_task(task_id: str) -> str:
    """Stop and clean up a task."""
    if task_id in tasks:
        del tasks[task_id]
        return f"Task {task_id} stopped and removed."
    return "Error: Task ID not found."

if __name__ == "__main__":
    log_debug("Server starting via mcp.run()...")
    mcp.run()