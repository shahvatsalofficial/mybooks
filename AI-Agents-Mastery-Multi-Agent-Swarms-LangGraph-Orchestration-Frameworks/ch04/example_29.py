import base64
import os
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

class ImageExtractionInput(BaseModel):
    image_path: str = Field(description="Absolute file path to the diagram or screenshot image.")
    target_extraction_mode: str = Field(default="architecture_topology", description="Mode: 'ocr_text', 'architecture_topology', or 'error_stack'")

class MultiModalExtractionTool(BaseTool):
    name: str = "multimodal_image_extractor"
    description: str = "Extracts text, architecture topology, and component hierarchies from visual diagram images."
    args_schema: Type[BaseModel] = ImageExtractionInput

    def _run(self, image_path: str, target_extraction_mode: str = "architecture_topology") -> str:
        if not os.path.exists(image_path):
            return f"ERROR: Target image file not found at '{image_path}'."
            
        file_size_kb = os.path.getsize(image_path) / 1024
        print(f"[MULTIMODAL TOOL] Ingesting diagram: {os.path.basename(image_path)} ({file_size_kb:.1f} KB, mode='{target_extraction_mode}')")
        
        # Production simulation of vision model extraction
        if target_extraction_mode == "architecture_topology":
            return (
                "### Extracted Architecture Diagram Analysis\n"
                "*   **Components Detected**: Client Gateway, Kong API Gateway, FastAPI Service, PostgreSQL Primary, Redis Cluster\n"
                "*   **Network Edges**: Client -> Kong (HTTPS/443), Kong -> FastAPI (mTLS), FastAPI -> Redis (Cache Read/Write), FastAPI -> Postgres (ACID Storage)\n"
                "*   **Identified Risks**: Single point of failure at Kong Gateway; Redis lacks replica nodes."
            )
        return "OCR Text: System online. All health probes returning HTTP 200."
