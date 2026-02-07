"""Tests for new image processing functions."""

import pytest
import numpy as np
from PIL import Image
from gel_boy.core.image_processing import (
    rotate_image, flip_image, invert_image,
    adjust_brightness, adjust_contrast
)


@pytest.fixture
def test_image():
    """Create a test image."""
    return Image.new('RGB', (100, 50), color=(128, 128, 128))


@pytest.fixture
def test_16bit_image(tmp_path):
    """Create a 16-bit test image."""
    # Create a 16-bit grayscale image with known values
    img_path = tmp_path / "test_16bit_invert.tif"
    data = np.full((50, 100), 30000, dtype=np.uint16)
    # Let PIL auto-detect mode from dtype
    img = Image.fromarray(data)
    img.save(img_path)
    # Load it back to get proper 16-bit mode and load into memory
    with Image.open(img_path) as loaded_img:
        loaded_img.load()  # Load data into memory
        return loaded_img


@pytest.fixture
def test_8bit_grayscale():
    """Create an 8-bit grayscale test image."""
    return Image.new('L', (100, 50), color=128)


def test_rotate_image(test_image):
    """Test image rotation."""
    # Rotate 90 degrees
    rotated = rotate_image(test_image, 90)
    assert rotated.size == (50, 100)  # Dimensions should swap
    
    # Rotate 180 degrees
    rotated_180 = rotate_image(test_image, 180)
    assert rotated_180.size == test_image.size
    
    # Rotate -90 degrees
    rotated_neg = rotate_image(test_image, -90)
    assert rotated_neg.size == (50, 100)


def test_flip_image(test_image):
    """Test image flipping."""
    # Horizontal flip
    flipped_h = flip_image(test_image, horizontal=True)
    assert flipped_h.size == test_image.size
    
    # Vertical flip
    flipped_v = flip_image(test_image, horizontal=False)
    assert flipped_v.size == test_image.size


def test_invert_image(test_image):
    """Test image inversion for RGB."""
    inverted = invert_image(test_image)
    assert inverted.size == test_image.size
    assert inverted.mode == 'RGB'


def test_invert_16bit_image(test_16bit_image):
    """Test image inversion for 16-bit images."""
    inverted = invert_image(test_16bit_image)
    
    # Check that size and mode are preserved
    assert inverted.size == test_16bit_image.size
    assert inverted.mode == test_16bit_image.mode
    
    # Check that inversion works correctly
    # Original image has value 30000, inverted should have 65535 - 30000 = 35535
    inverted_array = np.array(inverted)
    original_array = np.array(test_16bit_image)
    
    # Verify inversion formula: max_value - original
    expected = 65535 - original_array
    np.testing.assert_array_equal(inverted_array, expected)


def test_invert_8bit_grayscale(test_8bit_grayscale):
    """Test image inversion for 8-bit grayscale images."""
    inverted = invert_image(test_8bit_grayscale)
    
    # Check that size and mode are preserved
    assert inverted.size == test_8bit_grayscale.size
    assert inverted.mode == 'L'
    
    # Check that inversion works correctly
    # Original image has value 128, inverted should have 255 - 128 = 127
    inverted_array = np.array(inverted)
    original_array = np.array(test_8bit_grayscale)
    
    # Verify inversion formula: 255 - original
    expected = 255 - original_array
    np.testing.assert_array_equal(inverted_array, expected)


def test_adjust_brightness(test_image):
    """Test brightness adjustment."""
    # Increase brightness
    brighter = adjust_brightness(test_image, 1.5)
    assert brighter.size == test_image.size
    
    # Decrease brightness
    darker = adjust_brightness(test_image, 0.5)
    assert darker.size == test_image.size


def test_adjust_contrast(test_image):
    """Test contrast adjustment."""
    # Increase contrast
    more_contrast = adjust_contrast(test_image, 1.5)
    assert more_contrast.size == test_image.size
    
    # Decrease contrast
    less_contrast = adjust_contrast(test_image, 0.5)
    assert less_contrast.size == test_image.size


def test_transformations_preserve_type(test_image):
    """Test that transformations return PIL Images."""
    assert isinstance(rotate_image(test_image, 90), Image.Image)
    assert isinstance(flip_image(test_image), Image.Image)
    assert isinstance(invert_image(test_image), Image.Image)
    assert isinstance(adjust_brightness(test_image, 1.0), Image.Image)
    assert isinstance(adjust_contrast(test_image, 1.0), Image.Image)
