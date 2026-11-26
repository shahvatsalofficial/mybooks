"""
Enterprise Generative Asset Forensic Quality & Matting Pipeline
Target: Python 3.10+ / Pillow / ImageHash / Rembg / OpenCV
"""

import os
import io
import imagehash
from PIL import Image, ImageStat
from rembg import remove
from typing import Dict, Any, Tuple, Optional


class AssetForensicAuditor:
    def __init__(self, hash_db_path: Optional[str] = None):
        self.known_hashes: Dict[str, imagehash.ImageHash] = {}
        if hash_db_path and os.path.exists(hash_db_path):
            self._load_hash_db(hash_db_path)

    def _load_hash_db(self, path: str) -> None:
        with open(path, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    self.known_hashes[parts[0]] = imagehash.hex_to_hash(parts[1])

    def compute_perceptual_hash(self, image: Image.Image) -> imagehash.ImageHash:
        """Computes 64-bit perceptual hash (pHash) based on Discrete Cosine Transform (DCT)."""
        return imagehash.phash(image)

    def detect_duplicate(self, candidate_hash: imagehash.ImageHash, threshold: int = 5) -> Tuple[bool, Optional[str]]:
        """Compares candidate pHash against database using Hamming distance."""
        for asset_id, known_hash in self.known_hashes.items():
            hamming_dist = candidate_hash - known_hash
            if hamming_dist <= threshold:
                return True, asset_id
        return False, None

    def analyze_entropy_and_contrast(self, image: Image.Image) -> Dict[str, float]:
        """Calculates image entropy, RMS contrast, and dynamic range."""
        stat = ImageStat.Stat(image.convert('L'))
        mean_lum = stat.mean[0]
        rms_contrast = stat.stddev[0]
        # Shannon entropy of grayscale histogram
        hist = image.convert('L').histogram()
        total_pixels = sum(hist)
        entropy = 0.0
        import math
        for count in hist:
            if count > 0:
                p = count / total_pixels
                entropy -= p * math.log2(p)

        return {
            "mean_luminance": float(mean_lum),
            "rms_contrast": float(rms_contrast),
            "shannon_entropy": float(entropy)
        }

    def extract_transparent_alpha_matting(self, input_image_path: str, output_png_path: str) -> str:
        """Executes automated AI background removal using U2Net salient object detection."""
        print(f"[MATTING] Removing background from: {input_image_path}...")
        with open(input_image_path, 'rb') as f:
            input_bytes = f.read()

        # Execute U2Net salient mask removal
        output_bytes = remove(input_bytes)
        matting_image = Image.open(io.BytesIO(output_bytes)).convert('RGBA')

        # Verify alpha channel presence
        alpha = matting_image.split()[-1]
        transparent_pixels = sum(1 for p in alpha.getdata() if p == 0)
        total_pixels = matting_image.width * matting_image.height
        transparency_ratio = transparent_pixels / total_pixels

        matting_image.save(output_png_path, format='PNG', optimize=True)
        print(f"[MATTING SUCCESS] Transparent asset saved to {output_png_path} ({transparency_ratio*100:.1f}% alpha mask).")
        return output_png_path

    def audit_and_catalog(self, image_path: str, asset_id: str) -> Dict[str, Any]:
        """Runs full quality audit across perceptual uniqueness, contrast, and dimensions."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Target image not found at {image_path}")

        with Image.open(image_path) as img:
            p_hash = self.compute_perceptual_hash(img)
            is_dup, matched_id = self.detect_duplicate(p_hash, threshold=4)
            metrics = self.analyze_entropy_and_contrast(img)

            # Store in hash register if unique
            if not is_dup:
                self.known_hashes[asset_id] = p_hash

            return {
                "asset_id": asset_id,
                "perceptual_hash": str(p_hash),
                "is_duplicate": is_dup,
                "matched_duplicate_id": matched_id,
                "dimensions": {"width": img.width, "height": img.height},
                "metrics": metrics,
                "quality_pass": (metrics["rms_contrast"] > 25.0) and (not is_dup)
            }
