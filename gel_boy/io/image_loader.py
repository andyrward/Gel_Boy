"""Image loading functions for various formats."""

from typing import Optional
import numpy as np
from pathlib import Path


def load_image(filepath: Path) -> Optional[np.ndarray]:
    """Load an image from file.
    
    Supports common formats: PNG, JPEG, TIFF, BMP, etc.
    
    Args:
        filepath: Path to image file
        
    Returns:
        Image data as numpy array, or None if loading fails
    """
    pass


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
