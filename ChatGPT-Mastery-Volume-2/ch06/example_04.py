"""
Multimodal Vision Fine-Tuning Dataset Preparer
Encodes local invoice images to base64 and verifies multimodal JSONL formatting.
Author: Vatsal Shah, Enterprise AI Architect
"""
import os
import json
import base64
from PIL import Image
import io

class MultimodalDatasetBuilder:
    @staticmethod
    def encode_image_to_base64(image_path: str, max_size: int = 1024) -> str:
        with Image.open(image_path) as img:
            # Resize image to maintain aspect ratio within max_size bounding box
            img.thumbnail((max_size, max_size))
            buffer = io.BytesIO()
            img.convert("RGB").save(buffer, format="JPEG", quality=85)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @classmethod
    def create_multimodal_sample(cls, image_path: str, prompt_text: str, target_json: dict) -> dict:
        base64_str = cls.encode_image_to_base64(image_path)
        return {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_str}"}
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": json.dumps(target_json)
                }
            ]
        }
