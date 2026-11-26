import imagehash
from PIL import Image

class PHashDeduplicator:
    def __init__(self, hamming_threshold=4):
        self.registry = {}
        self.threshold = hamming_threshold

    def register_and_check_duplicate(self, asset_id: str, image_path: str):
        with Image.open(image_path) as img:
            current_hash = imagehash.phash(img)
            for existing_id, existing_hash in self.registry.items():
                distance = current_hash - existing_hash
                if distance <= self.threshold:
                    return False, f"Near-duplicate of existing asset {existing_id} (distance={distance})"
            
            self.registry[asset_id] = current_hash
            return True, f"Unique asset registered (pHash={current_hash})"

dedup = PHashDeduplicator(hamming_threshold=4)
is_valid, msg = dedup.register_and_check_duplicate("PROD-001", "/mnt/data/chair_render_v1.png")
print(f"Asset Status: {is_valid} | {msg}")
