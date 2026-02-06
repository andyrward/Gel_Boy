"""Tests for image loader module."""

import pytest
from pathlib import Path
from PIL import Image
from gel_boy.io.image_loader import load_image, get_image_info, get_supported_formats


@pytest.fixture
def test_image_path(tmp_path):
    """Create a temporary test image."""
    img_path = tmp_path / "test.png"
    img = Image.new('RGB', (200, 150), color=(100, 100, 100))
    img.save(img_path)
    return str(img_path)


def test_load_image_success(test_image_path):
    """Test successful image loading."""
    img = load_image(test_image_path)
    assert img is not None
    assert isinstance(img, Image.Image)
    assert img.size == (200, 150)


def test_load_image_invalid_path():
    """Test loading non-existent image."""
    img = load_image("/nonexistent/path/image.png")
    assert img is None


def test_get_image_info():
    """Test getting image information."""
    img = Image.new('RGB', (300, 200), color=(50, 50, 50))
    info = get_image_info(img)
    
    assert info['width'] == 300
    assert info['height'] == 200
    assert info['size'] == (300, 200)
    assert info['mode'] == 'RGB'


def test_get_supported_formats():
    """Test getting supported formats."""
    formats = get_supported_formats()
    assert isinstance(formats, list)
    assert len(formats) > 0
    assert "*.png" in formats
    assert "*.tif" in formats or "*.tiff" in formats
    assert "*.jpg" in formats or "*.jpeg" in formats


def test_load_grayscale_image(tmp_path):
    """Test loading grayscale image."""
    img_path = tmp_path / "gray.png"
    img = Image.new('L', (100, 100), color=128)
    img.save(img_path)
    
    loaded = load_image(str(img_path))
    assert loaded is not None
    assert loaded.mode in ('L', 'RGB')  # May be converted
