"""
Enterprise High-DPI Document Tiling Engine
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Opportunity4u Press (c) 2026
"""

from PIL import Image
import io
import math

class DocumentTilingEngine:
    def __init__(self, tile_size: int = 768):
        self.tile_size = tile_size

    def tile_image(self, image_bytes: bytes) -> list[bytes]:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        # Calculate optimal grid
        cols = math.ceil(width / self.tile_size)
        rows = math.ceil(height / self.tile_size)
        
        tiles = []
        for r in range(rows):
            for c in range(cols):
                box = (
                    c * self.tile_size,
                    r * self.tile_size,
                    min((c + 1) * self.tile_size, width),
                    min((r + 1) * self.tile_size, height)
                )
                tile = img.crop(box)
                out = io.BytesIO()
                tile.save(out, format="PNG")
                tiles.append(out.getvalue())
                
        return tiles
