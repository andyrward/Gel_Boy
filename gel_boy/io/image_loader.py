"""Image file loading utilities."""

from typing import Optional, List
import numpy as np
from pathlib import Path
from PIL import Image


SUPPORTED_FORMATS = [
    "*.tif", "*.tiff",  # TIFF (common for scientific imaging)
    "*.png",            # PNG
    "*.jpg", "*.jpeg",  # JPEG
    "*.bmp",            # BMP
    "*.gif"             # GIF
]


def load_image(filepath: str) -> Optional[Image.Image]:
    """Load an image file.
    
    Args:
        filepath: Path to image file
        
    Returns:
        PIL Image if successful, None if failed
    """
    try:
        image = Image.open(filepath)
        # Convert to RGB if needed (handles RGBA, grayscale, etc.)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        return image
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


def get_image_info(image: Image.Image) -> dict:
    """Get information about an image.
    
    Args:
        image: PIL Image
        
    Returns:
        Dictionary with image metadata (size, mode, format, etc.)
    """
    info = {
        'width': image.width,
        'height': image.height,
        'mode': image.mode,
        'format': image.format,
        'size': image.size
    }
    return info


def get_supported_formats() -> List[str]:
    """Get list of supported image formats for file dialogs.
    
    Returns:
        List of file extension patterns
    """
    return SUPPORTED_FORMATS


# Legacy numpy-based functions kept for backward compatibility
def load_tiff_stack(filepath: Path) -> Optional[np.ndarray]:
    """Load a multi-page TIFF stack.
    
    Args:
        filepath: Path to TIFF file
        
    Returns:
        3D numpy array (stack, height, width), or None if loading fails
    """
    pass


def get_image_metadata(filepath: Path) -> dict:
    """Extract metadata from image file.
    
    Args:
        filepath: Path to image file
        
    Returns:
        Dictionary of metadata
    """
    pass


def validate_image_format(filepath: Path) -> bool:
    """Check if file is a supported image format.
    
    Args:
        filepath: Path to image file
        
    Returns:
        True if format is supported, False otherwise
    """
    pass
