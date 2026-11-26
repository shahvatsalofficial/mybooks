# clinical_dicom_processor.py
import pydicom
import numpy as np
from PIL import Image

def normalize_dicom_to_png(dicom_file_path: str, window_center: int = -600, window_width: int = 1500) -> Image.Image:
    """Applies Hounsfield Unit (HU) windowing to CT/X-Ray DICOM slices for radiological inspection."""
    dcm = pydicom.dcmread(dicom_file_path)
    pixel_array = dcm.pixel_array.astype(float)
    
    # Rescale slope and intercept
    slope = getattr(dcm, 'RescaleSlope', 1)
    intercept = getattr(dcm, 'RescaleIntercept', 0)
    hu_image = pixel_array * slope + intercept
    
    # Apply radiological windowing
    img_min = window_center - window_width // 2
    img_max = window_center + window_width // 2
    windowed = np.clip(hu_image, img_min, img_max)
    normalized = ((windowed - img_min) / (img_max - img_min) * 255.0).astype(np.uint8)
    
    return Image.fromarray(normalized)
