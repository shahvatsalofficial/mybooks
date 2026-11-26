# image_roi_preprocessor.py — Smart Multimodal Preprocessing
import math
from PIL import Image
from typing import List, Tuple

class MultimodalTileOptimizer:
    TILE_SIZE = 512

    @staticmethod
    def calculate_token_cost(width: int, height: int, detail: str = "high") -> int:
        """Calculates exact GPT-4o vision token billing cost."""
        if detail == "low":
            return 85

        # 1. Scale shortest side to 768px, capping long side at 2048px
        aspect = width / height
        if width < height:
            new_w = 768
            new_h = int(768 / aspect)
        else:
            new_h = 768
            new_w = int(768 * aspect)

        if new_w > 2048:
            new_w = 2048
            new_h = int(2048 / aspect)
        elif new_h > 2048:
            new_h = 2048
            new_w = int(2048 * aspect)

        # 2. Count 512x512 tiles
        tiles_x = math.ceil(new_w / 512)
        tiles_y = math.ceil(new_h / 512)
        total_tiles = tiles_x * tiles_y

        return 85 + (total_tiles * 170)

    @staticmethod
    def crop_bounding_box(image_path: str, bbox_norm: List[int], out_path: str):
        """
        Crops image using normalized coordinates [ymin, xmin, ymax, xmax] in [0, 1000] space.
        """
        with Image.open(image_path) as img:
            w, h = img.size
            ymin, xmin, ymax, xmax = bbox_norm
            left = int((xmin / 1000.0) * w)
            top = int((ymin / 1000.0) * h)
            right = int((xmax / 1000.0) * w)
            bottom = int((ymax / 1000.0) * h)

            cropped = img.crop((left, top, right, bottom))
            cropped.save(out_path, quality=95)
