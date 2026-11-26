"""
Enterprise Architectural Blueprint Collision Detector
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Opportunity4u Press (c) 2026
"""

import base64
import json
import logging
from typing import List
from pydantic import BaseModel, Field
import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BlueprintDetector")

class SpatialCollision(BaseModel):
    collision_id: str
    subsystem_a: str = Field(..., description="E.g. High-Voltage Electrical Conduit")
    subsystem_b: str = Field(..., description="E.g. Cryogenic Medical Gas Piping")
    severity: str = Field(..., description="CRITICAL, MAJOR, or MINOR")
    bounding_box: List[int] = Field(..., description="[ymin, xmin, ymax, xmax] 0-1000 grid")
    code_violation_rationale: str
    recommended_rerouting: str

class BlueprintAuditReport(BaseModel):
    sheet_number: str
    total_collisions_found: int
    collisions: List[SpatialCollision]

class BlueprintCollisionDetector:
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def audit_blueprint_sheet(self, image_path: str, sheet_id: str) -> BlueprintAuditReport:
        with open(image_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode("utf-8")

        schema_json = json.dumps(BlueprintAuditReport.model_json_schema(), indent=2)

        system_prompt = f"""<system_instructions>
You are a Principal MEP Building Systems Engineer and Forensic Inspector.
Audit the provided architectural blueprint schematic for mechanical, electrical, and plumbing collisions.
Adhere strictly to this Pydantic schema:
<schema>
{schema_json}
</schema>
Rules:
1. Provide normalized [ymin, xmin, ymax, xmax] coordinates for every detected collision.
2. Output ONLY the raw JSON object enclosed in <collision_report> tags.
</system_instructions>"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.0,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": "image/png", "data": b64_img}
                        },
                        {"type": "text", "text": f"Audit blueprint sheet {sheet_id} for physical collisions."}
                    ]
                },
                {"role": "assistant", "content": "<collision_report>{"}
            ]
        )

        raw_out = "<collision_report>{" + response.content[0].text
        json_str = raw_out.split("<collision_report>")[1].split("</collision_report>")[0].strip()
        return BlueprintAuditReport.model_validate_json(json_str)
