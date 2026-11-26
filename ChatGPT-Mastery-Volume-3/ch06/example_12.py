# vla_gui_agent.py
import json
import pyautogui
from PIL import Image
import io
import base64
from openai import AzureOpenAI

class EnterpriseGUIAgent:
    def __init__(self, client: AzureOpenAI, model: str = "gpt-4o"):
        self.client = client
        self.model = model

    def capture_screen_base64(self) -> str:
        screenshot = pyautogui.screenshot()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    async def execute_task_step(self, user_goal: str) -> dict:
        img_base64 = self.capture_screen_base64()
        
        system_prompt = (
            "You are an enterprise GUI automation agent. Inspect the current application screenshot and the user goal. "
            "Determine the next atomic UI action required (CLICK, TYPE, SCROLL, WAIT, COMPLETE). "
            "Return normalized coordinates (0 to 1000) for bounding boxes and target click locations. "
            "Output strictly formatted JSON adhering to the GUI action schema."
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Current Goal: {user_goal}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": "high"}}
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        action_plan = json.loads(response.choices[0].message.content)
        self._dispatch_os_action(action_plan)
        return action_plan

    def _dispatch_os_action(self, plan: dict):
        action = plan.get("action")
        screen_w, screen_h = pyautogui.size()
        
        if action == "CLICK":
            norm_x, norm_y = plan["coordinates"]["x"], plan["coordinates"]["y"]
            abs_x = int((norm_x / 1000.0) * screen_w)
            abs_y = int((norm_y / 1000.0) * screen_h)
            pyautogui.moveTo(abs_x, abs_y, duration=0.25)
            pyautogui.click()
            
        elif action == "TYPE":
            pyautogui.write(plan.get("text", ""), interval=0.05)
            if plan.get("press_enter"):
                pyautogui.press("enter")
