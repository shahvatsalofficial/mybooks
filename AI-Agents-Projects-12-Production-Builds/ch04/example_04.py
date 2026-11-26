from __future__ import annotations

from html.parser import HTMLParser
from typing import List
from pydantic import BaseModel


class ParsedFinancialTable(BaseModel):
    table_id: str
    caption: str
    unit_scale: str
    headers: List[str]
    rows: List[List[str]]

    def to_markdown(self) -> str:
        header_line = "| " + " | ".join(self.headers) + " |"
        sep_line = "| " + " | ".join("---" for _ in self.headers) + " |"
        body_lines = ["| " + " | ".join(r) + " |" for r in self.rows]
        return "\n".join([f"**{self.caption} ({self.unit_scale})**", header_line, sep_line, *body_lines])


class _SimpleTableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: List[List[str]] = []
        self._current_row: List[str] = []
        self._in_cell = False
        self._cell_buf: List[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "tr":
            self._current_row = []
        elif tag in ("td", "th"):
            self._in_cell = True
            self._cell_buf = []

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_buf.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th"):
            self._in_cell = False
            self._current_row.append(" ".join(self._cell_buf).strip())
        elif tag == "tr" and self._current_row:
            self.rows.append(self._current_row)


class FinancialTableParser:
    """Extracts HTML tables into atomic header-bound financial structures."""

    @staticmethod
    def parse(table_id: str, caption: str, unit_scale: str, html_str: str) -> ParsedFinancialTable:
        parser = _SimpleTableHTMLParser()
        parser.feed(html_str)
        if not parser.rows:
            raise ValueError("No table rows extracted from HTML.")
        headers = parser.rows[0]
        data_rows = parser.rows[1:]
        return ParsedFinancialTable(
            table_id=table_id,
            caption=caption,
            unit_scale=unit_scale,
            headers=headers,
            rows=data_rows,
        )


if __name__ == "__main__":
    html_sample = """
    <table>
      <tr><th>Line Item</th><th>FY2025</th><th>FY2024</th></tr>
      <tr><td>Operating Cash Flow</td><td>$3,120</td><td>$2,640</td></tr>
      <tr><td>Capital Expenditures</td><td>(1,420)</td><td>(980)</td></tr>
    </table>
    """
    tbl = FinancialTableParser.parse(
        "tbl_cf_01", "Consolidated Cash Flows", "USD in millions", html_sample
    )
    print(tbl.to_markdown())
