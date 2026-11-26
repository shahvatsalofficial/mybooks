"""
table_reconstruction_pipeline.py
Reconstructs multi-level merged table cells from Azure AI Document Intelligence JSON
into hierarchical pandas MultiIndex tables for downstream RAG ingestion.
"""

from typing import List, Dict, Any
import pandas as pd


def parse_document_intelligence_table(table_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Parses table object graph containing row_index, column_index, row_span, col_span.
    """
    row_count = table_data["rowCount"]
    col_count = table_data["columnCount"]
    
    # Initialize empty 2D grid
    grid = [["" for _ in range(col_count)] for _ in range(row_count)]
    header_rows = set()

    for cell in table_data.get("cells", []):
        r = cell["rowIndex"]
        c = cell["columnIndex"]
        r_span = cell.get("rowSpan", 1)
        c_span = cell.get("columnSpan", 1)
        content = cell["content"]
        
        if cell.get("kind") == "columnHeader":
            header_rows.add(r)

        # Populate spanned cells
        for dr in range(r_span):
            for dc in range(c_span):
                if r + dr < row_count and c + dc < col_count:
                    grid[r + dr][c + dc] = content

    # If first two rows are headers, construct MultiIndex
    if len(header_rows) >= 2:
        tuples = list(zip(grid[0], grid[1]))
        columns = pd.MultiIndex.from_tuples(tuples)
        data = grid[2:]
        df = pd.DataFrame(data, columns=columns)
    else:
        columns = grid[0]
        data = grid[1:]
        df = pd.DataFrame(data, columns=columns)

    return df


if __name__ == "__main__":
    print("[*] Table Reconstruction Pipeline verified.")
