# industrial_defect_inspector.py
import cv2
import json
import base64
from openai import AzureOpenAI

class ManufacturingQualityInspector:
    def __init__(self, client: AzureOpenAI):
        self.client = client

    def inspect_pcb_solder_joint(self, high_res_frame) -> dict:
        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', high_res_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        
        system_prompt = (
            "You are an expert electronics quality assurance AI. Inspect the provided high-resolution PCB micro-inspection image. "
            "Identify solder bridging, tombstoning, cold solder joints, missing surface mount components, or pin misalignment. "
            "Return structured JSON with severity scores (PASS, WARN, REJECT) and root cause diagnostic summaries."
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Perform automated solder joint quality inspection."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}", "detail": "high"}}
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        return json.loads(response.choices[0].message.content)
