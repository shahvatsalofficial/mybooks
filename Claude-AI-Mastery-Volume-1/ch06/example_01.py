"""
Enterprise Multimodal PDF Statement Extractor
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Vatsal Shah (c) 2026
"""

import os
import io
import json
import base64
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import fitz  # PyMuPDF
import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MultimodalExtractor")

class BoundingBox(BaseModel):
    ymin: int = Field(..., ge=0, le=1000)
    xmin: int = Field(..., ge=0, le=1000)
    ymax: int = Field(..., ge=0, le=1000)
    xmax: int = Field(..., ge=0, le=1000)

class StatementLineItem(BaseModel):
    description: str
    amount: float
    currency: str
    category: str
    bounding_box: BoundingBox

class ExtractedFinancialStatement(BaseModel):
    institution_name: str
    statement_period: str
    account_number_redacted: str
    total_debits: float
    total_credits: float
    closing_balance: float
    line_items: List[StatementLineItem]

class EnterprisePDFExtractor:
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-3-5-sonnet-20241022"

    def render_pdf_page_to_base64(self, pdf_path: str, page_number: int = 0, dpi: int = 150) -> str:
        """
        Renders a specific PDF page into a high-DPI PNG image encoded in Base64.
        """
        doc = fitz.open(pdf_path)
        if page_number >= len(doc):
            raise IndexError(f"Page {page_number} exceeds document length ({len(doc)} pages).")
        
        page = doc[page_number]
        # Calculate matrix zoom factor for target DPI (72 DPI is standard 1.0 zoom)
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        
        img_bytes = pix.tobytes("png")
        doc.close()
        return base64.b64encode(img_bytes).decode("utf-8")

    def extract_statement(self, pdf_path: str, page_number: int = 0) -> ExtractedFinancialStatement:
        """
        Extracts structured financial line items and spatial bounding boxes from a PDF page.
        """
        logger.info(f"Rendering page {page_number} of {pdf_path} at 150 DPI...")
        b64_image = self.render_pdf_page_to_base64(pdf_path, page_number=page_number, dpi=150)

        schema_json = json.dumps(ExtractedFinancialStatement.model_json_schema(), indent=2)

        system_prompt = f"""<system_instructions>
You are an expert forensic accountant and multimodal vision analyst.
Extract all financial statement data from the provided image page.
Adhere strictly to this Pydantic JSON schema:
<schema>
{schema_json}
</schema>
Rules:
1. Provide spatial bounding boxes on a [ymin, xmin, ymax, xmax] 0-1000 normalized grid for every line item.
2. Output ONLY the raw JSON object enclosed in <extracted_data> tags.
3. Never emit conversational preambles or markdown code fences.
</system_instructions>"""

        logger.info("Dispatching multimodal request to Claude 3.5 Sonnet...")
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
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": b64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": "Extract all statement line items, balances, and spatial bounding boxes."
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": "<extracted_data>{" # Assistant prefill to collapse generation entropy
                }
            ]
        )

        raw_response = "<extracted_data>{" + response.content[0].text
        # Parse content between XML tags
        json_str = raw_response.split("<extracted_data>")[1].split("</extracted_data>")[0].strip()
        
        parsed_data = ExtractedFinancialStatement.model_validate_json(json_str)
        logger.info(f"Successfully extracted {len(parsed_data.line_items)} line items with spatial coordinates.")
        return parsed_data

# Production Verification Script
if __name__ == "__main__":
    print("Enterprise Multimodal PDF Statement Extractor initialized.")
