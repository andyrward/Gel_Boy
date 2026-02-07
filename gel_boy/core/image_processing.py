"""Core image processing functions for gel analysis."""

from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from gel_boy.io.image_loader import get_bit_depth


def rotate_image(image: Image.Image, angle: int) -> Image.Image:
    """Rotate image by specified angle (legacy for 90-degree rotations).
    
    Args:
        image: PIL Image to rotate
        angle: Rotation angle (90, 180, 270, or -90)
        
    Returns:
        Rotated PIL Image
    """
    return image.rotate(-angle, expand=True)


def rotate_image_precise(
    image: Image.Image,
    angle: float,
    expand: bool = True,
    fillcolor: Optional[Tuple[int, int, int]] = None
) -> Image.Image:
    """Rotate image by precise decimal angle.
    
    Args:
        image: PIL Image to rotate
        angle: Rotation angle in degrees (positive = counter-clockwise)
        expand: If True, expand output to fit entire rotated image
        fillcolor: Color for areas outside original image (default: black for RGB, 0 for grayscale)
        
    Returns:
        Rotated PIL Image
    """
    # PIL's rotate uses counter-clockwise angles
    # If fillcolor not specified, use appropriate default
    if fillcolor is None:
        if image.mode == 'RGB' or image.mode == 'RGBA':
            fillcolor = (0, 0, 0)
        else:
            fillcolor = 0
    
    return image.rotate(angle, expand=expand, fillcolor=fillcolor, resample=Image.BICUBIC)


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
    
    Works with 16-bit, 8-bit grayscale, and RGB images.
    
    Args:
        image: PIL Image to invert
        
    Returns:
        Inverted PIL Image
    """
    # Check bit depth
    bit_depth, max_value = get_bit_depth(image)
    
    if bit_depth == 16:
        # For 16-bit images, manually invert using numpy
        img_array = np.array(image)
        inverted_array = max_value - img_array
        # Let PIL auto-detect mode from dtype
        return Image.fromarray(inverted_array)
    elif image.mode == 'L':
        # For 8-bit grayscale, use ImageOps.invert directly
        return ImageOps.invert(image)
    else:
        # For RGB and other modes, convert to RGB and invert
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


def apply_intensity_window(
    image: Image.Image,
    min_val: int,
    max_val: int
) -> Image.Image:
    """Apply intensity windowing (min/max clipping) to image.
    
    Remaps pixel intensities so that min_val becomes 0 and max_val becomes 255,
    with linear interpolation in between. Values outside this range are clipped.
    
    Args:
        image: PIL Image to adjust
        min_val: Minimum intensity value (0-255)
        max_val: Maximum intensity value (0-255)
        
    Returns:
        Windowed PIL Image
    """
    # Ensure min < max
    if min_val >= max_val:
        return image
    
    # Convert to numpy array
    img_array = np.array(image)
    
    # Create lookup table
    lut = np.arange(256, dtype=np.float32)
    
    # Apply windowing: map [min_val, max_val] to [0, 255]
    lut = (lut - min_val) * 255.0 / (max_val - min_val)
    lut = np.clip(lut, 0, 255).astype(np.uint8)
    
    # Apply LUT to image
    if len(img_array.shape) == 2:
        # Grayscale
        result = lut[img_array]
    elif len(img_array.shape) == 3:
        # RGB - apply to each channel
        result = np.zeros_like(img_array)
        for i in range(img_array.shape[2]):
            result[:, :, i] = lut[img_array[:, :, i]]
    else:
        return image
    
    return Image.fromarray(result, mode=image.mode)


def calculate_histogram(image: Image.Image) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate histogram for image.
    
    For grayscale images, returns a single histogram.
    For RGB images, returns combined histogram of all channels.
    For 16-bit images, uses 256 bins covering the full range.
    
    Args:
        image: PIL Image
        
    Returns:
        Tuple of (bins, values) where:
        - For 8-bit: bins are 0-255, values are counts per bin
        - For 16-bit: bins are 256 points from 0-65535, values are counts per bin
    """
    img_array = np.array(image)
    
    # Determine if this is 16-bit data
    is_16bit = image.mode in ('I', 'I;16')
    
    if is_16bit:
        # For 16-bit images, use 256 bins spanning 0-65535
        if len(img_array.shape) == 2:
            # Grayscale 16-bit
            hist, bins = np.histogram(img_array.flatten(), bins=256, range=(0, 65536))
        else:
            # Shouldn't happen for 16-bit, but handle anyway
            hist, bins = np.histogram(img_array.flatten(), bins=256, range=(0, 65536))
        # Return bin centers instead of edges
        bin_centers = (bins[:-1] + bins[1:]) / 2
        return bin_centers, hist
    else:
        # 8-bit images
        if len(img_array.shape) == 2:
            # Grayscale
            hist, bins = np.histogram(img_array.flatten(), bins=256, range=(0, 256))
        elif len(img_array.shape) == 3:
            # RGB - combine all channels
            hist, bins = np.histogram(img_array.flatten(), bins=256, range=(0, 256))
        else:
            # Fallback
            hist = np.zeros(256)
            bins = np.arange(257)
        
        return bins[:-1], hist


def apply_lut_adjustments(
    image: Image.Image,
    min_val: int = 0,
    max_val: int = 255,
    brightness: float = 1.0,
    contrast: float = 1.0
) -> Image.Image:
    """Apply combined LUT-based adjustments for performance.
    
    Combines intensity windowing, brightness, and contrast into a single LUT
    for efficient application. Works with both 8-bit and 16-bit images.
    
    Args:
        image: PIL Image to adjust
        min_val: Minimum intensity value (0-255 for 8-bit, 0-65535 for 16-bit)
        max_val: Maximum intensity value (0-255 for 8-bit, 0-65535 for 16-bit)
        brightness: Brightness factor (1.0 = original)
        contrast: Contrast factor (1.0 = original)
        
    Returns:
        Adjusted PIL Image
    """
    from gel_boy.io.image_loader import get_bit_depth
    
    # Get bit depth info
    bit_depth, max_possible = get_bit_depth(image)
    
    # Ensure min < max
    if min_val >= max_val:
        min_val = 0
        max_val = max_possible
    
    # Convert image to numpy array
    img_array = np.array(image)
    
    if bit_depth == 16:
        # For 16-bit images, apply windowing directly on data
        # Convert to float for calculations
        data = img_array.astype(np.float32)
        
        # Apply intensity windowing: map [min_val, max_val] to [0, 255]
        data = np.clip(data, min_val, max_val)
        data = ((data - min_val) / (max_val - min_val) * 255.0)
        
        # Apply contrast around midpoint (128)
        if abs(contrast - 1.0) > 0.01:
            data = (data - 128) * contrast + 128
        
        # Apply brightness
        if abs(brightness - 1.0) > 0.01:
            data = data * brightness
        
        # Clip to 8-bit range
        data = np.clip(data, 0, 255).astype(np.uint8)
        
        # Return as 8-bit grayscale image
        return Image.fromarray(data, mode='L')
    else:
        # For 8-bit images, use LUT approach
        # Create base LUT
        lut = np.arange(256, dtype=np.float32)
        
        # Apply intensity windowing
        lut = (lut - min_val) * 255.0 / (max_val - min_val)
        lut = np.clip(lut, 0, 255)
        
        # Apply contrast around midpoint (128)
        if abs(contrast - 1.0) > 0.01:
            lut = (lut - 128) * contrast + 128
        
        # Apply brightness
        if abs(brightness - 1.0) > 0.01:
            lut = lut * brightness
        
        # Clip to valid range
        lut = np.clip(lut, 0, 255).astype(np.uint8)
        
        # Apply LUT
        if len(img_array.shape) == 2:
            # Grayscale
            result = lut[img_array]
        elif len(img_array.shape) == 3:
            # RGB - apply to each channel
            result = np.zeros_like(img_array)
            for i in range(img_array.shape[2]):
                result[:, :, i] = lut[img_array[:, :, i]]
        else:
            return image
        
        return Image.fromarray(result, mode=image.mode)


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
