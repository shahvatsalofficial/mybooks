"""
Enterprise Multi-Tier Entity Extraction Gateway
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Opportunity4u Press (c) 2026
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError
import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ExtractionGateway")

class InvoiceLineItem(BaseModel):
    item_description: str
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0.0)
    total_amount: float = Field(..., ge=0.0)

class EnterpriseInvoicePayload(BaseModel):
    invoice_number: str = Field(..., regex=r"^[A-Z0-9\-]+$")
    vendor_name: str
    invoice_date: str = Field(..., regex=r"^\d{4}-\d{2}-\d{2}$") # ISO-8601 YYYY-MM-DD
    total_tax_amount: float
    grand_total_amount: float
    line_items: list[InvoiceLineItem]

class MultiTierExtractionGateway:
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.haiku_model = "claude-3-5-haiku-20241022"
        self.sonnet_model = "claude-3-5-sonnet-20241022"

    def _execute_extraction(self, model: str, raw_text: str, error_context: Optional[str] = None) -> Tuple[bool, Optional[EnterpriseInvoicePayload], str]:
        schema_json = json.dumps(EnterpriseInvoicePayload.model_json_schema(), indent=2)
        
        system_prompt = f"""<system_instructions>
You are a zero-defect enterprise financial data extractor.
Extract all invoice data from the source text into this exact JSON schema:
<schema>
{schema_json}
</schema>
Rules:
1. Dates must strictly follow ISO-8601 format (YYYY-MM-DD).
2. Output ONLY the raw JSON object enclosed in <extracted_invoice> tags.
3. Never emit markdown code fences or conversational pleasantries.
</system_instructions>"""

        user_content = f"<raw_document>\n{raw_text}\n</raw_document>"
        if error_context:
            user_content += f"\n<previous_validation_error>\n{error_context}\nPlease correct the schema violations.\n</previous_validation_error>"

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0.0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": "<extracted_invoice>{"}
                ]
            )
            raw_text_out = "<extracted_invoice>{" + response.content[0].text
            json_str = raw_text_out.split("<extracted_invoice>")[1].split("</extracted_invoice>")[0].strip()
            
            payload = EnterpriseInvoicePayload.model_validate_json(json_str)
            return True, payload, "SUCCESS"
        except ValidationError as ve:
            return False, None, str(ve)
        except Exception as e:
            return False, None, f"API Exception: {str(e)}"

    def extract_with_multi_tier_fallback(self, raw_document: str) -> EnterpriseInvoicePayload:
        # Tier 1: High-Speed Haiku Pass
        logger.info("Tier 1: Attempting high-speed extraction with Claude 3.5 Haiku...")
        success, payload, err = self._execute_extraction(self.haiku_model, raw_document)
        if success:
            logger.info("Tier 1 SUCCESS: Haiku extracted valid payload.")
            return payload

        # Tier 2: Frontier Sonnet Pass
        logger.warning(f"Tier 1 Failed ({err}). Escalating to Tier 2: Claude 3.5 Sonnet...")
        success, payload, err = self._execute_extraction(self.sonnet_model, raw_document)
        if success:
            logger.info("Tier 2 SUCCESS: Sonnet extracted valid payload.")
            return payload

        # Tier 3: Surgical Self-Correction Pass
        logger.warning(f"Tier 2 Failed ({err}). Attempting Tier 3: Surgical Self-Correction with Sonnet...")
        success, payload, final_err = self._execute_extraction(self.sonnet_model, raw_document, error_context=err)
        if success:
            logger.info("Tier 3 SUCCESS: Sonnet self-corrected payload.")
            return payload

        # Tier 4: DLQ Quarantine
        logger.error(f"Tier 3 Failed permanently: {final_err}. Quarantining to Dead-Letter Queue.")
        raise RuntimeError(f"Extraction failed across all tiers: {final_err}")
