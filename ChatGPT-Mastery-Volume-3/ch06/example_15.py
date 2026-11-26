# agentic_multimodal_investigator.py
import json
from openai import AzureOpenAI
from PIL import Image
import io
import base64

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "crop_and_enhance_region",
            "description": "Crops a high-resolution sub-region of an image and applies adaptive histogram equalization.",
            "parameters": {
                "type": "object",
                "properties": {
                    "box_2d": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "[ymin, xmin, ymax, xmax] normalized coordinates (0-1000)"
                    },
                    "enhancement_mode": {"type": "string", "enum": ["CLAHE", "EDGE_SOBEL", "SHARPEN"]}
                },
                "required": ["box_2d", "enhancement_mode"]
            }
        }
    }
]

class MultimodalAgentInvestigator:
    def __init__(self, client: AzureOpenAI):
        self.client = client

    def run_investigation_loop(self, base_image_b64: str, target_question: str) -> str:
        messages = [
            {"role": "system", "content": "You are an autonomous engineering visual investigator. Use tools to crop and enhance ambiguous visual regions before making a final diagnostic determination."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": target_question},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base_image_b64}", "detail": "high"}}
                ]
            }
        ]

        for step in range(3): # Maximum 3 investigation turns
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.1
            )
            
            choice = response.choices[0]
            if choice.message.tool_calls:
                # Handle tool execution
                tool_call = choice.message.tool_calls[0]
                args = json.loads(tool_call.function.arguments)
                print(f"Agent requested tool: {tool_call.function.name} with coordinates: {args['box_2d']}")
                
                # Execute crop and simulate tool return
                messages.append(choice.message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps({"status": "SUCCESS", "analysis": "Micro-fracture detected along structural weld line."})
                })
            else:
                return choice.message.content
                
        return "Investigation exceeded maximum allowed visual reasoning turns."
