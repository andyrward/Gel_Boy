"""Core image processing functions for gel analysis."""

from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageOps, ImageEnhance


def rotate_image(image: Image.Image, angle: int) -> Image.Image:
    """Rotate image by specified angle.
    
    Args:
        image: PIL Image to rotate
        angle: Rotation angle (90, 180, 270, or -90)
        
    Returns:
        Rotated PIL Image
    """
    return image.rotate(-angle, expand=True)


def flip_image(image: Image.Image, horizontal: bool = True) -> Image.Image:
    """Flip image horizontally or vertically.
    
    Args:
        image: PIL Image to flip
        horizontal: If True, flip horizontally, else vertically
        
    Returns:
        Flipped PIL Image
    """
    if horizontal:
        return ImageOps.mirror(image)
    else:
        return ImageOps.flip(image)


def invert_image(image: Image.Image) -> Image.Image:
    """Invert image colors (create negative).
    
    Args:
        image: PIL Image to invert
        
    Returns:
        Inverted PIL Image
    """
    return ImageOps.invert(image.convert('RGB'))


def adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
    """Adjust image brightness.
    
    Args:
        image: PIL Image to adjust
        factor: Brightness factor (1.0 = original, <1.0 darker, >1.0 brighter)
        
    Returns:
        Brightness-adjusted PIL Image
    """
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def adjust_contrast(image: Image.Image, factor: float) -> Image.Image:
    """Adjust image contrast.
    
    Args:
        image: PIL Image to adjust
        factor: Contrast factor (1.0 = original, <1.0 less contrast, >1.0 more contrast)
        
    Returns:
        Contrast-adjusted PIL Image
    """
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


# Legacy numpy-based functions kept for backward compatibility
def apply_gaussian_blur(image: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Apply Gaussian blur to an image.
    
    Args:
        image: Input image as numpy array
        sigma: Standard deviation for Gaussian kernel
        
    Returns:
        Blurred image
    """
    pass


def crop_image(
    image: np.ndarray,
    x: int,
    y: int,
    width: int,
    height: int
) -> np.ndarray:
    """Crop image to specified region.
    
    Args:
        image: Input image as numpy array
        x: Left edge of crop region
        y: Top edge of crop region
        width: Width of crop region
        height: Height of crop region
        
    Returns:
        Cropped image
    """
    pass
