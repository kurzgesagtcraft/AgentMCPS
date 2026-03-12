import os
import time
import subprocess

class AndroidController:
    def __init__(self, adb_path):
        self.adb_path = adb_path

    def execute_adb(self, command):
        full_command = f"{self.adb_path} {command}"
        # log_debug(f"Executing ADB: {full_command}")
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            with open("mobile_agent_debug.log", "a", encoding="utf-8") as f:
                f.write(f"ADB Error: {result.stderr}\n")
        return result

    def get_screenshot(self, save_path):
        # Try direct screencap to stdout first for speed, or fallback to file
        res = self.execute_adb("shell screencap -p > /sdcard/screenshot.png")
        self.execute_adb(f"pull /sdcard/screenshot.png {save_path}")
        if not os.path.exists(save_path) or os.path.getsize(save_path) == 0:
            # Fallback: some devices need different redirection or paths
            self.execute_adb(f"shell screencap -p {save_path}") # This only works if adb has local write access, unlikely
            # Try another path
            self.execute_adb("shell screencap -p /data/local/tmp/screenshot.png")
            self.execute_adb(f"pull /data/local/tmp/screenshot.png {save_path}")
        return os.path.exists(save_path) and os.path.getsize(save_path) > 0

    def tap(self, x, y):
        self.execute_adb(f"shell input tap {x} {y}")

    def slide(self, x1, y1, x2, y2):
        self.execute_adb(f"shell input swipe {x1} {y1} {x2} {y2}")

    def type(self, text):
        # Replace spaces with %s for adb input
        text = text.replace(" ", "%s")
        self.execute_adb(f"shell input text {text}")

    def back(self):
        self.execute_adb("shell input keyevent 4")

    def home(self):
        self.execute_adb("shell input keyevent 3")

class HarmonyOSController:
    def __init__(self, hdc_path):
        self.hdc_path = hdc_path

    def execute_hdc(self, command):
        full_command = f"{self.hdc_path} {command}"
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
        return result

    def get_screenshot(self, save_path):
        self.execute_hdc("shell snapshot_display -p /data/local/tmp/screenshot.png")
        self.execute_hdc(f"file recv /data/local/tmp/screenshot.png {save_path}")
        return os.path.exists(save_path)

    def tap(self, x, y):
        self.execute_hdc(f"shell input tap {x} {y}")

    def slide(self, x1, y1, x2, y2):
        self.execute_hdc(f"shell input swipe {x1} {y1} {x2} {y2}")

    def type(self, text):
        self.execute_hdc(f"shell input text {text}")

    def back(self):
        self.execute_hdc("shell input keyevent 4")

    def home(self):
        self.execute_hdc("shell input keyevent 3")

class WindowsController:
    def __init__(self):
        import pyautogui
        self.pyautogui = pyautogui
        self.pyautogui.FAILSAFE = False

    def get_screenshot(self, save_path):
        try:
            screenshot = self.pyautogui.screenshot()
            screenshot.save(save_path)
            return os.path.exists(save_path)
        except Exception as e:
            with open("mobile_agent_debug.log", "a", encoding="utf-8") as f:
                f.write(f"Windows Screenshot Error: {str(e)}\n")
            return False

    def tap(self, x, y):
        self.pyautogui.click(x, y)

    def slide(self, x1, y1, x2, y2):
        self.pyautogui.moveTo(x1, y1)
        self.pyautogui.dragTo(x2, y2, duration=0.5)

    def type(self, text):
        self.pyautogui.write(text)

    def back(self):
        # Windows doesn't have a universal 'back', use Alt+Left or Esc as fallback
        self.pyautogui.hotkey('alt', 'left')

    def home(self):
        # Windows key
        self.pyautogui.press('win')