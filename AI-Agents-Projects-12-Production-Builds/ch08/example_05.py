from __future__ import annotations

from enum import Enum
from typing import List
from pydantic import BaseModel


class PageRoute(str, Enum):
    TEXT_CHUNKER = "text_chunker"
    VISION_VLM = "vision_vlm"
    TABLE_PARSER = "table_parser"


class PageLayoutMetrics(BaseModel):
    page_number: int
    char_count: int
    image_count: int
    vector_rect_count: int
    has_grid_lines: bool = False


class MultiModalPageRouter:
    """Routes PDF pages between fast text chunking, table parsing, and Vision-LLM."""

    def route_page(self, metrics: PageLayoutMetrics) -> PageRoute:
        if metrics.has_grid_lines and metrics.char_count > 120:
            return PageRoute.TABLE_PARSER
        if metrics.image_count >= 1 or metrics.vector_rect_count >= 8 or metrics.char_count < 150:
            return PageRoute.VISION_VLM
        return PageRoute.TEXT_CHUNKER


def demo_page_router() -> None:
    router = MultiModalPageRouter()
    pages = [
        PageLayoutMetrics(page_number=1, char_count=2100, image_count=0, vector_rect_count=0),
        PageLayoutMetrics(page_number=2, char_count=95, image_count=1, vector_rect_count=14),
        PageLayoutMetrics(page_number=3, char_count=840, image_count=0, vector_rect_count=18, has_grid_lines=True),
    ]
    for p in pages:
        print(f"Page {p.page_number} -> {router.route_page(p).value}")


if __name__ == "__main__":
    demo_page_router()
