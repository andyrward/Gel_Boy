"""Image file loading utilities."""

from typing import Optional, List, Tuple
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
    
    Preserves 16-bit images ('I', 'I;16') and 8-bit images ('RGB', 'L').
    Other modes are converted to RGB.
    
    Args:
        filepath: Path to image file
        
    Returns:
        PIL Image if successful, None if failed
    """
    try:
        image = Image.open(filepath)
        # Keep RGB, grayscale (L), and 16-bit modes (I, I;16) intact
        # Convert other modes (RGBA, P, etc.) to RGB
        if image.mode not in ('RGB', 'L', 'I', 'I;16'):
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


def get_bit_depth(image: Image.Image) -> Tuple[int, int]:
    """Get bit depth and maximum value for an image.
    
    Args:
        image: PIL Image
    
    Returns:
        Tuple of (bit_depth, max_value)
        - For 8-bit images: (8, 255)
        - For 16-bit images: (16, 65535)
    """
    if image.mode == 'L':
        return (8, 255)
    elif image.mode in ('I', 'I;16'):
        return (16, 65535)
    elif image.mode == 'RGB':
        return (8, 255)
    else:
        return (8, 255)


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
