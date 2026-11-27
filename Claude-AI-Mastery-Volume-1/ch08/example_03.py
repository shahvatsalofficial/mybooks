"""
Enterprise Universal ETL Kafka Daemon
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Vatsal Shah (c) 2026
"""

import json
import logging
from typing import Optional
from pydantic import BaseModel, Field
import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("UniversalETL")

class CleanedTelemetryEvent(BaseModel):
    event_id: str
    source_service: str
    severity: str
    root_cause_category: str
    extracted_metrics: dict[str, float]
    action_required: bool

class UniversalETLDaemon:
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-haiku-20241022"

    def process_raw_log_message(self, raw_unstructured_log: str) -> CleanedTelemetryEvent:
        schema_json = json.dumps(CleanedTelemetryEvent.model_json_schema(), indent=2)
        
        system_prompt = f"""<system_instructions>
Transform the raw unstructured server log into this exact JSON schema:
<schema>
{schema_json}
</schema>
Emit ONLY the raw JSON object enclosed in <event> tags.
</system_instructions>"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"<raw_log>\n{raw_unstructured_log}\n</raw_log>"},
                {"role": "assistant", "content": "<event>{"}
            ]
        )

        raw_out = "<event>{" + response.content[0].text
        json_str = raw_out.split("<event>")[1].split("</event>")[0].strip()
        
        return CleanedTelemetryEvent.model_validate_json(json_str)
