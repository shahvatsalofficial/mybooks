# document_table_stitcher.py — Multi-Page Financial Table Extraction
import os
from typing import List, Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest

class EnterpriseDocumentStitcher:
    def __init__(self, endpoint: str, key: str):
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )

    def extract_tables_as_markdown(self, file_path: str) -> List[str]:
        """Parses PDF and extracts clean markdown tables."""
        with open(file_path, "rb") as f:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-layout",
                analyze_request=f,
                output_content_format="markdown",
                content_type="application/octet-stream"
            )
        result: AnalyzeResult = poller.result()
        markdown_tables = []

        if not result.tables:
            return markdown_tables

        for table_idx, table in enumerate(result.tables):
            # Construct row-column grid
            rows = table.row_count
            cols = table.column_count
            grid = [["" for _ in range(cols)] for _ in range(rows)]

            for cell in table.cells:
                r = cell.row_index
                c = cell.column_index
                grid[r][c] = cell.content.replace("\n", " ").strip()

            # Render GitHub Flavored Markdown Table
            md_lines = []
            header = "| " + " | ".join(grid[0]) + " |"
            separator = "| " + " | ".join(["---"] * cols) + " |"
            md_lines.append(header)
            md_lines.append(separator)

            for row in grid[1:]:
                row_str = "| " + " | ".join(row) + " |"
                md_lines.append(row_str)

            markdown_tables.append("\n".join(md_lines))

        return markdown_tables
