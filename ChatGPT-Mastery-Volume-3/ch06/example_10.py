# multimodal_document_processor.py
import io
import base64
from PIL import Image
from openai import AzureOpenAI

class MultimodalDocumentIngestor:
    def __init__(self, endpoint: str, api_key: str, api_version: str = "2024-08-01-preview"):
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )

    def prepare_image_payload(self, image_bytes: bytes) -> str:
        # Load and validate image dimensions
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        # Enforce RGB color profile for consistent tokenization
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=92)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    async def extract_blueprint_components(self, image_base64: str) -> dict:
        system_prompt = (
            "You are an enterprise structural engineering AI. Inspect the provided architectural blueprint. "
            "Extract all dimensional measurements, structural load callouts, material schedules, and spatial relationships. "
            "Output your findings in structured JSON adhering strictly to the provided architectural schema."
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Parse this blueprint and extract structural elements with bounding box coordinates."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=4096
        )
        
        return json.loads(response.choices[0].message.content)
