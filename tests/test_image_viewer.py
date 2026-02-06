"""Tests for image viewer widget."""

import pytest
from PIL import Image
from PyQt6.QtWidgets import QApplication
from gel_boy.gui.widgets.image_viewer import ImageViewer
from gel_boy.io.image_loader import load_image


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def test_image():
    """Create a test image."""
    return Image.new('RGB', (100, 100), color=(128, 128, 128))


def test_image_viewer_initialization(qapp):
    """Test ImageViewer initialization."""
    viewer = ImageViewer()
    assert viewer.original_image is None
    assert viewer.current_image is None
    assert viewer.zoom_level == 1.0
    assert not viewer.has_image()


def test_image_viewer_load_image(qapp, test_image):
    """Test loading an image into viewer."""
    viewer = ImageViewer()
    viewer.load_image(test_image)
    
    assert viewer.has_image()
    assert viewer.original_image is not None
    assert viewer.current_image is not None
    assert viewer.original_image.size == test_image.size


def test_image_viewer_zoom(qapp, test_image):
    """Test zoom functionality."""
    viewer = ImageViewer()
    viewer.load_image(test_image)
    
    # Test zoom in
    initial_zoom = viewer.zoom_level
    viewer.zoom_in()
    assert viewer.zoom_level > initial_zoom
    
    # Test zoom out
    current_zoom = viewer.zoom_level
    viewer.zoom_out()
    assert viewer.zoom_level < current_zoom
    
    # Test set zoom
    viewer.set_zoom(2.0)
    assert viewer.zoom_level == 2.0


def test_image_viewer_reset(qapp, test_image):
    """Test reset to original image."""
    viewer = ImageViewer()
    viewer.load_image(test_image)
    
    original_size = viewer.current_image.size
    
    # Apply transformation (rotate changes dimensions for non-square images)
    from gel_boy.core.image_processing import rotate_image
    viewer.apply_transformation(rotate_image, 90)
    
    # Reset should restore original
    viewer.reset_image()
    assert viewer.current_image.size == original_size
