"""Tests for new image processing functions."""

import pytest
from PIL import Image
from gel_boy.core.image_processing import (
    rotate_image, flip_image, invert_image,
    adjust_brightness, adjust_contrast
)


@pytest.fixture
def test_image():
    """Create a test image."""
    return Image.new('RGB', (100, 50), color=(128, 128, 128))


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
    """Test image inversion."""
    inverted = invert_image(test_image)
    assert inverted.size == test_image.size
    assert inverted.mode == 'RGB'


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
