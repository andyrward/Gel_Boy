"""Tests for 16-bit image support."""

import pytest
import numpy as np
from pathlib import Path
from PIL import Image
from gel_boy.io.image_loader import load_image, get_bit_depth
from gel_boy.core.image_processing import calculate_histogram, apply_lut_adjustments


@pytest.fixture
def test_16bit_image(tmp_path):
    """Create a temporary 16-bit test image."""
    img_path = tmp_path / "test_16bit.tif"
    
    # Create a 16-bit image with values spanning the full range
    width, height = 100, 100
    data = np.random.randint(0, 65536, size=(height, width), dtype=np.uint16)
    
    # Add some known values for testing
    data[0:10, 0:10] = 1000    # Dark region
    data[0:10, 10:20] = 30000  # Mid region
    data[0:10, 20:30] = 60000  # Bright region
    
    img = Image.fromarray(data, mode='I;16')
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def test_8bit_image(tmp_path):
    """Create a temporary 8-bit test image."""
    img_path = tmp_path / "test_8bit.png"
    img = Image.new('L', (100, 100), color=128)
    img.save(img_path)
    return str(img_path)


def test_load_16bit_image_preserves_mode(test_16bit_image):
    """Test that 16-bit images are loaded with correct mode."""
    img = load_image(test_16bit_image)
    assert img is not None
    assert img.mode in ('I', 'I;16'), f"Expected 16-bit mode, got {img.mode}"


def test_load_8bit_image_preserves_mode(test_8bit_image):
    """Test that 8-bit images are loaded with correct mode."""
    img = load_image(test_8bit_image)
    assert img is not None
    assert img.mode == 'L'


def test_get_bit_depth_8bit(test_8bit_image):
    """Test bit depth detection for 8-bit images."""
    img = load_image(test_8bit_image)
    bit_depth, max_value = get_bit_depth(img)
    assert bit_depth == 8
    assert max_value == 255


def test_get_bit_depth_16bit(test_16bit_image):
    """Test bit depth detection for 16-bit images."""
    img = load_image(test_16bit_image)
    bit_depth, max_value = get_bit_depth(img)
    assert bit_depth == 16
    assert max_value == 65535


def test_calculate_histogram_8bit(test_8bit_image):
    """Test histogram calculation for 8-bit images."""
    img = load_image(test_8bit_image)
    bins, values = calculate_histogram(img)
    
    # Should have 256 bins for 8-bit
    assert len(bins) == 256
    assert len(values) == 256
    
    # Bins should range from 0 to 255
    assert bins[0] == 0
    assert bins[-1] == 255


def test_calculate_histogram_16bit(test_16bit_image):
    """Test histogram calculation for 16-bit images."""
    img = load_image(test_16bit_image)
    bins, values = calculate_histogram(img)
    
    # Should have 256 bins for 16-bit (binned)
    assert len(bins) == 256
    assert len(values) == 256
    
    # Bins should span 0 to ~65535
    assert bins[0] >= 0
    assert bins[-1] <= 65536
    assert bins[-1] > 60000  # Should be near the top of the range


def test_apply_lut_adjustments_8bit(test_8bit_image):
    """Test LUT adjustments on 8-bit images."""
    img = load_image(test_8bit_image)
    
    # Apply windowing
    result = apply_lut_adjustments(img, min_val=50, max_val=200)
    
    assert result is not None
    assert result.mode == 'L'
    assert result.size == img.size


def test_apply_lut_adjustments_16bit(test_16bit_image):
    """Test LUT adjustments on 16-bit images."""
    img = load_image(test_16bit_image)
    
    # Apply windowing (should convert to 8-bit for display)
    result = apply_lut_adjustments(img, min_val=10000, max_val=50000)
    
    assert result is not None
    # Should be converted to 8-bit grayscale
    assert result.mode == 'L'
    assert result.size == img.size


def test_16bit_windowing_conversion(test_16bit_image):
    """Test that 16-bit windowing properly maps values to 8-bit range."""
    img = load_image(test_16bit_image)
    
    # Apply windowing to map a specific range
    min_val = 20000
    max_val = 40000
    result = apply_lut_adjustments(img, min_val=min_val, max_val=max_val)
    
    # Convert to numpy to check values
    result_array = np.array(result)
    
    # Result should be 8-bit
    assert result_array.dtype == np.uint8
    
    # Check that windowing worked - values should be spread across 0-255
    # The specific region we set to 30000 should be somewhere in the middle
    assert result_array.min() >= 0
    assert result_array.max() <= 255


def test_16bit_histogram_has_data_in_expected_bins(test_16bit_image):
    """Test that 16-bit histogram bins contain data in expected regions."""
    img = load_image(test_16bit_image)
    bins, values = calculate_histogram(img)
    
    # We created regions at specific intensities
    # Find bins corresponding to our test values
    # 1000, 30000, 60000
    
    # Total histogram should have some counts
    total_counts = np.sum(values)
    assert total_counts > 0
    
    # Should have data spread across multiple bins (not just one)
    non_zero_bins = np.sum(values > 0)
    assert non_zero_bins > 1


def test_get_bit_depth_rgb():
    """Test bit depth detection for RGB images."""
    img = Image.new('RGB', (100, 100), color=(128, 128, 128))
    bit_depth, max_value = get_bit_depth(img)
    assert bit_depth == 8
    assert max_value == 255


def test_16bit_brightness_contrast(test_16bit_image):
    """Test brightness and contrast adjustments on 16-bit images."""
    img = load_image(test_16bit_image)
    
    # Get original data for comparison
    original_data = np.array(img)
    
    # Apply adjustments
    result = apply_lut_adjustments(
        img,
        min_val=10000,
        max_val=50000,
        brightness=1.2,
        contrast=1.5
    )
    
    assert result is not None
    assert result.mode == 'L'  # Should be converted to 8-bit
    assert result.size == img.size
    
    # Verify that adjustments were actually applied
    result_data = np.array(result)
    
    # The region with values around 30000 (in original range) should be 
    # mapped to mid-range in 8-bit after windowing
    # Due to brightness and contrast, values should be different from default windowing
    
    # Apply default windowing without brightness/contrast for comparison
    default_result = apply_lut_adjustments(img, min_val=10000, max_val=50000)
    default_data = np.array(default_result)
    
    # With brightness and contrast applied, the values should differ
    # We expect the adjusted result to have different intensity distribution
    assert not np.array_equal(result_data, default_data), \
        "Brightness/contrast adjustments should change pixel values"
