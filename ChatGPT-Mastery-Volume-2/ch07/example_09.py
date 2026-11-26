"""
Enterprise Spatial PII Redaction Engine
Detects sensitive visual bounding boxes and applies irreversible pixel masking.
Author: Vatsal Shah, Enterprise AI Architect
"""
from PIL import Image, ImageDraw
from typing import List, Tuple

def redact_sensitive_bounding_boxes(
    image_path: str,
    redaction_boxes: List[Tuple[int, int, int, int]], # (top_y, left_x, bottom_y, right_x) in 0-1000 norm
    output_path: str
) -> str:
    """Irreversibly applies solid black masks over sensitive document coordinates."""
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    for top_norm, left_norm, bot_norm, right_norm in redaction_boxes:
        # Convert normalized 0-1000 coordinates to actual pixel coordinates
        x0 = int((left_norm / 1000.0) * w)
        y0 = int((top_norm / 1000.0) * h)
        x1 = int((right_norm / 1000.0) * w)
        y1 = int((bot_norm / 1000.0) * h)
        
        # Apply solid black rectangle fill with 2px security padding
        draw.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], fill=(0, 0, 0))

    img.save(output_path, "JPEG", quality=85)
    print(f"🔒 Irreversibly redacted {len(redaction_boxes)} sensitive zones on {output_path}")
    return output_path
