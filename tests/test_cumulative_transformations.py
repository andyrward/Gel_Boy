"""Tests for cumulative image transformations.

Tests that verify adjustments (brightness/contrast) preserve previous
transformations (invert, rotate, flip) without resetting to original.

These tests verify the image processing functions work correctly when
applied cumulatively.
"""

import pytest
from PIL import Image
import numpy as np
from gel_boy.core.image_processing import invert_image, apply_lut_adjustments


@pytest.fixture
def test_image_8bit():
    """Create an 8-bit grayscale test image."""
    # Create a simple gradient image
    data = np.arange(0, 256, dtype=np.uint8).reshape(16, 16)
    return Image.fromarray(data, mode='L')


@pytest.fixture
def test_image_16bit():
    """Create a 16-bit test image.
    
    Note: PIL mode 'I' expects int32 data, but we use unsigned values
    0-65535 to represent 16-bit image data (as is typical for medical/scientific imaging).
    """
    # Create a simple gradient image with 16-bit values
    # Mode 'I' expects int32, so we convert from uint16 range to int32
    data = np.arange(0, 65536, 256, dtype=np.int32).reshape(16, 16)
    return Image.fromarray(data, mode='I')


def test_invert_then_brightness_8bit(test_image_8bit):
    """Test that applying brightness after invert works on the inverted image."""
    # Get original pixel value at a specific location
    original_value = test_image_8bit.getpixel((8, 8))
    
    # Apply invert transformation
    inverted_image = invert_image(test_image_8bit)
    inverted_value = inverted_image.getpixel((8, 8))
    
    # Verify inversion worked (inverted should be 255 - original)
    assert inverted_value == 255 - original_value, "Inversion failed"
    
    # Apply brightness adjustment to the inverted image
    adjusted_image = apply_lut_adjustments(inverted_image, 0, 255, 1.2, 1.0)
    adjusted_value = adjusted_image.getpixel((8, 8))
    
    # The adjusted value should be based on the inverted image
    # Calculate what we expect: inverted * brightness
    expected_value = int(min(255, inverted_value * 1.2))
    
    # Allow small tolerance for rounding
    assert abs(adjusted_value - expected_value) <= 2, \
        f"Brightness not applied correctly to inverted image. Expected ~{expected_value}, got {adjusted_value}"


def test_invert_then_contrast_8bit(test_image_8bit):
    """Test that applying contrast after invert works on the inverted image."""
    # Apply invert transformation
    inverted_image = invert_image(test_image_8bit)
    inverted_image_array = np.array(inverted_image)
    
    # Apply contrast adjustment to the inverted image
    adjusted_image = apply_lut_adjustments(inverted_image, 0, 255, 1.0, 1.5)
    adjusted_image_array = np.array(adjusted_image)
    
    # The adjusted image should still be inverted (dark pixels should be light)
    # Check that the overall intensity pattern matches inverted, not original
    # Original has increasing values (top-left dark, bottom-right bright)
    # Inverted has decreasing values (top-left bright, bottom-right dark)
    # So after inversion, top-left should be brighter than bottom-right
    assert adjusted_image_array[0, 0] > adjusted_image_array[-1, -1], \
        "Contrast not applied to inverted image - image appears to be reset to original"


def test_invert_then_windowing_8bit(test_image_8bit):
    """Test that applying windowing after invert works on the inverted image."""
    # Apply invert transformation
    inverted_image = invert_image(test_image_8bit)
    inverted_image_array = np.array(inverted_image)
    
    # Apply windowing (min/max adjustment) to the inverted image
    adjusted_image = apply_lut_adjustments(inverted_image, 50, 200, 1.0, 1.0)
    adjusted_image_array = np.array(adjusted_image)
    
    # The adjusted image should still be inverted
    # After inversion, top-left should be brighter than bottom-right
    assert adjusted_image_array[0, 0] > adjusted_image_array[-1, -1], \
        "Windowing not applied to inverted image - image appears to be reset to original"


def test_invert_then_combined_adjustments_8bit(test_image_8bit):
    """Test that combined adjustments work on inverted image."""
    # Apply invert transformation
    inverted_image = invert_image(test_image_8bit)
    
    # Apply combined windowing, brightness and contrast to the inverted image
    adjusted_image = apply_lut_adjustments(inverted_image, 50, 200, 1.2, 1.3)
    adjusted_image_array = np.array(adjusted_image)
    
    # The adjusted image should still show the inverted pattern
    assert adjusted_image_array[0, 0] > adjusted_image_array[-1, -1], \
        "Combined adjustments not applied to inverted image - image appears to be reset to original"


def test_invert_16bit_then_brightness(test_image_16bit):
    """Test that applying brightness after invert works on 16-bit images."""
    # Get original value
    original_value = test_image_16bit.getpixel((8, 8))
    
    # Apply invert to 16-bit image
    inverted_image = invert_image(test_image_16bit)
    inverted_value = inverted_image.getpixel((8, 8))
    
    # Verify inversion (16-bit inversion: 65535 - original)
    # Allow small tolerance due to potential rounding in numpy operations
    assert abs(inverted_value - (65535 - original_value)) <= 1, "16-bit inversion failed"
    
    # Apply brightness via LUT adjustments
    # For 16-bit, apply_lut_adjustments converts to 8-bit
    adjusted_image = apply_lut_adjustments(inverted_image, 0, 65535, 1.2, 1.0)
    
    # After adjustment, image should be 8-bit (as per apply_lut_adjustments behavior)
    assert adjusted_image.mode == 'L', "16-bit image should convert to 8-bit after LUT adjustments"
    
    # The key test: the image should still reflect the inversion
    # After inversion, the gradient should be reversed
    image_array = np.array(adjusted_image)
    # Original 16-bit image had increasing values, so after inversion it should have decreasing
    # After conversion to 8-bit and brightness, it should still have that pattern
    assert image_array[0, 0] > image_array[-1, -1], \
        "Brightness not applied to inverted 16-bit image - image appears to be reset to original"


def test_mode_preserved_after_invert_8bit(test_image_8bit):
    """Test that image mode is preserved after inversion for 8-bit images."""
    # Verify original is 8-bit 'L' mode
    assert test_image_8bit.mode == 'L'
    
    # Apply inversion
    inverted_image = invert_image(test_image_8bit)
    
    # Inverted image should still be 8-bit 'L' mode
    assert inverted_image.mode == 'L', "Inversion changed image mode unexpectedly"


def test_mode_preserved_after_invert_16bit(test_image_16bit):
    """Test that image mode is preserved after inversion for 16-bit images."""
    # Verify original is 16-bit 'I' mode
    assert test_image_16bit.mode == 'I'
    
    # Apply inversion
    inverted_image = invert_image(test_image_16bit)
    
    # Inverted image should still be 16-bit 'I' mode
    assert inverted_image.mode == 'I', "Inversion changed 16-bit image mode unexpectedly"

