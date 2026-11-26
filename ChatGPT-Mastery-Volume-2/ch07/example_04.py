"""
Production Visual Document Understanding (VDU) Pipeline
Extracts structured financial invoice items and spatial bounding boxes.
Author: Vatsal Shah, Enterprise AI Architect
"""
import base64
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI

client = OpenAI()

class LineItem(BaseModel):
    description: str = Field(description="Description of the goods or services.")
    quantity: float = Field(description="Numeric quantity billed.")
    unit_price: float = Field(description="Price per individual unit.")
    total_price: float = Field(description="Line item total.")

class InvoiceExtractionSchema(BaseModel):
    invoice_number: str = Field(description="The unique invoice identifier string.")
    invoice_date: str = Field(description="Date formatted as YYYY-MM-DD.")
    vendor_name: str = Field(description="Legal entity name of the vendor.")
    currency: str = Field(description="ISO 4217 3-letter currency code (e.g. USD).")
    tax_amount: float = Field(description="Total sales tax or VAT.")
    grand_total: float = Field(description="Grand total payable balance.")
    line_items: List[LineItem] = Field(description="Detailed itemized breakdown.")

def parse_scanned_invoice(image_path: str) -> InvoiceExtractionSchema:
    with open(image_path, "rb") as img_file:
        b64_data = base64.b64encode(img_file.read()).decode("utf-8")

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert institutional invoice parsing engine. "
                    "Analyze the provided scanned visual document and extract all fields according to the schema. "
                    "Do not guess missing information; leave string fields empty if not present."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all data from this commercial invoice."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_data}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        response_format=InvoiceExtractionSchema,
        temperature=0.0
    )

    return completion.choices[0].message.parsed
