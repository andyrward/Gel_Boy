"""Tests for enhanced image processing functions."""

import pytest
import numpy as np
from PIL import Image
from gel_boy.core.image_processing import (
    rotate_image_precise,
    apply_intensity_window,
    calculate_histogram,
    apply_lut_adjustments
)


def create_test_grayscale_image(width=100, height=100):
    """Create a test grayscale image."""
    # Create gradient image
    array = np.linspace(0, 255, width * height, dtype=np.uint8).reshape(height, width)
    return Image.fromarray(array, mode='L')


def create_test_rgb_image(width=100, height=100):
    """Create a test RGB image."""
    # Create gradient image for each channel
    r = np.linspace(0, 255, width * height, dtype=np.uint8).reshape(height, width)
    g = np.linspace(255, 0, width * height, dtype=np.uint8).reshape(height, width)
    b = np.full((height, width), 128, dtype=np.uint8)
    array = np.stack([r, g, b], axis=2)
    return Image.fromarray(array, mode='RGB')


class TestRotateImagePrecise:
    """Tests for precise rotation function."""
    
    def test_rotate_0_degrees(self):
        """Test rotation by 0 degrees."""
        img = create_test_grayscale_image(50, 50)
        rotated = rotate_image_precise(img, 0.0)
        assert rotated.size == img.size
        
    def test_rotate_90_degrees(self):
        """Test rotation by 90 degrees."""
        img = create_test_grayscale_image(100, 50)
        rotated = rotate_image_precise(img, 90.0, expand=True)
        # When rotated 90 degrees with expand, dimensions swap
        assert rotated.width == 50
        assert rotated.height == 100
        
    def test_rotate_45_degrees_expand(self):
        """Test rotation by 45 degrees with expand."""
        img = create_test_grayscale_image(100, 100)
        rotated = rotate_image_precise(img, 45.0, expand=True)
        # Rotated image should be larger than original
        assert rotated.width > img.width
        assert rotated.height > img.height
        
    def test_rotate_45_degrees_no_expand(self):
        """Test rotation by 45 degrees without expand."""
        img = create_test_grayscale_image(100, 100)
        rotated = rotate_image_precise(img, 45.0, expand=False)
        # Rotated image should be same size as original
        assert rotated.size == img.size
        
    def test_rotate_negative_angle(self):
        """Test rotation by negative angle."""
        img = create_test_grayscale_image(100, 100)
        rotated = rotate_image_precise(img, -45.5, expand=True)
        assert rotated is not None
        assert rotated.width > 0
        
    def test_rotate_with_fillcolor_rgb(self):
        """Test rotation with custom fill color for RGB image."""
        img = create_test_rgb_image(50, 50)
        rotated = rotate_image_precise(img, 45.0, expand=True, fillcolor=(255, 255, 255))
        assert rotated.mode == 'RGB'
        
    def test_rotate_with_fillcolor_grayscale(self):
        """Test rotation with custom fill color for grayscale image."""
        img = create_test_grayscale_image(50, 50)
        rotated = rotate_image_precise(img, 45.0, expand=True, fillcolor=255)
        assert rotated.mode == 'L'


class TestApplyIntensityWindow:
    """Tests for intensity windowing function."""
    
    def test_window_full_range(self):
        """Test windowing with full range (0-255)."""
        img = create_test_grayscale_image()
        windowed = apply_intensity_window(img, 0, 255)
        # Should be identical to original
        assert np.array_equal(np.array(img), np.array(windowed))
        
    def test_window_narrow_range(self):
        """Test windowing with narrow range."""
        img = create_test_grayscale_image()
        windowed = apply_intensity_window(img, 100, 200)
        arr = np.array(windowed)
        # After windowing, values should use full 0-255 range
        assert arr.min() == 0
        assert arr.max() == 255
        
    def test_window_rgb_image(self):
        """Test windowing on RGB image."""
        img = create_test_rgb_image()
        windowed = apply_intensity_window(img, 50, 200)
        assert windowed.mode == 'RGB'
        assert windowed.size == img.size
        
    def test_window_invalid_range(self):
        """Test windowing with invalid range (min >= max)."""
        img = create_test_grayscale_image()
        windowed = apply_intensity_window(img, 200, 100)
        # Should return unchanged image
        assert np.array_equal(np.array(img), np.array(windowed))
        
    def test_window_min_equals_max(self):
        """Test windowing with min equals max."""
        img = create_test_grayscale_image()
        windowed = apply_intensity_window(img, 128, 128)
        # Should return unchanged image
        assert np.array_equal(np.array(img), np.array(windowed))


class TestCalculateHistogram:
    """Tests for histogram calculation function."""
    
    def test_histogram_grayscale(self):
        """Test histogram calculation for grayscale image."""
        img = create_test_grayscale_image()
        bins, values = calculate_histogram(img)
        assert len(bins) == 256
        assert len(values) == 256
        assert bins[0] == 0
        assert bins[-1] == 255
        
    def test_histogram_rgb(self):
        """Test histogram calculation for RGB image."""
        img = create_test_rgb_image()
        bins, values = calculate_histogram(img)
        assert len(bins) == 256
        assert len(values) == 256
        
    def test_histogram_sum(self):
        """Test that histogram sum equals number of pixels."""
        img = create_test_grayscale_image(100, 100)
        bins, values = calculate_histogram(img)
        total = np.sum(values)
        assert total == 100 * 100  # Total pixels
        
    def test_histogram_uniform_image(self):
        """Test histogram for uniform image."""
        # Create image with all pixels at value 128
        array = np.full((100, 100), 128, dtype=np.uint8)
        img = Image.fromarray(array, mode='L')
        bins, values = calculate_histogram(img)
        # All values should be in bin 128
        assert values[128] == 100 * 100
        assert np.sum(values) - values[128] == 0


class TestApplyLutAdjustments:
    """Tests for combined LUT adjustments function."""
    
    def test_lut_no_adjustments(self):
        """Test LUT with default values (no change)."""
        img = create_test_grayscale_image()
        adjusted = apply_lut_adjustments(img, 0, 255, 1.0, 1.0)
        # Should be identical or very close to original
        diff = np.abs(np.array(img).astype(float) - np.array(adjusted).astype(float))
        assert np.mean(diff) < 1.0  # Allow small rounding differences
        
    def test_lut_brightness_increase(self):
        """Test LUT with increased brightness."""
        img = create_test_grayscale_image()
        adjusted = apply_lut_adjustments(img, 0, 255, 1.5, 1.0)
        # Average intensity should increase
        assert np.mean(np.array(adjusted)) > np.mean(np.array(img))
        
    def test_lut_brightness_decrease(self):
        """Test LUT with decreased brightness."""
        img = create_test_grayscale_image()
        adjusted = apply_lut_adjustments(img, 0, 255, 0.5, 1.0)
        # Average intensity should decrease
        assert np.mean(np.array(adjusted)) < np.mean(np.array(img))
        
    def test_lut_contrast_increase(self):
        """Test LUT with increased contrast."""
        img = create_test_grayscale_image()
        adjusted = apply_lut_adjustments(img, 0, 255, 1.0, 1.5)
        # Standard deviation should increase with more contrast
        assert np.std(np.array(adjusted)) > np.std(np.array(img))
        
    def test_lut_windowing(self):
        """Test LUT with intensity windowing."""
        img = create_test_grayscale_image()
        adjusted = apply_lut_adjustments(img, 100, 200, 1.0, 1.0)
        arr = np.array(adjusted)
        # After windowing, range should be expanded
        assert arr.min() == 0
        assert arr.max() == 255
        
    def test_lut_combined_adjustments(self):
        """Test LUT with all adjustments combined."""
        img = create_test_grayscale_image()
        adjusted = apply_lut_adjustments(img, 50, 200, 1.2, 1.3)
        assert adjusted.size == img.size
        assert adjusted.mode == img.mode
        
    def test_lut_rgb_image(self):
        """Test LUT on RGB image."""
        img = create_test_rgb_image()
        adjusted = apply_lut_adjustments(img, 50, 200, 1.2, 1.1)
        assert adjusted.mode == 'RGB'
        assert adjusted.size == img.size
        
    def test_lut_invalid_window(self):
        """Test LUT with invalid window (min >= max)."""
        img = create_test_grayscale_image()
        adjusted = apply_lut_adjustments(img, 200, 100, 1.0, 1.0)
        # Should use default range 0-255
        assert adjusted is not None
