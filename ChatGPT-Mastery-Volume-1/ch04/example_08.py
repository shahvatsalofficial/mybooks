from rembg import remove
from PIL import Image
import io

def extract_alpha_isolated_asset(source_jpg: str, output_png: str):
    with open(source_jpg, 'rb') as f:
        input_data = f.read()
    
    # Remove background with U2Net salient boundary extraction
    transparent_output = remove(input_data)
    
    img = Image.open(io.BytesIO(transparent_output))
    # Crop bounding box to strip excess transparent padding
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        
    img.save(output_png, format="PNG", optimize=True)
    print(f"Isolated transparent asset saved to: {output_png}")

extract_alpha_isolated_asset('/mnt/data/shoe_studio_render.png', '/mnt/data/shoe_transparent_isolated.png')
