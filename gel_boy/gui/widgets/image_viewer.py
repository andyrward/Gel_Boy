"""Custom image display widget for gel electrophoresis images."""

from typing import Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
import numpy as np


class ImageViewer(QWidget):
    """Custom widget for displaying and interacting with gel images.
    
    Provides zoom, pan, and annotation capabilities for gel electrophoresis images.
    """
    
    image_clicked = pyqtSignal(int, int)  # Emits x, y coordinates
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the image viewer.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.image: Optional[np.ndarray] = None
        self.zoom_level: float = 1.0
        
    def load_image(self, image_data: np.ndarray) -> None:
        """Load an image into the viewer.
        
        Args:
            image_data: Image data as numpy array
        """
        pass
        
    def set_zoom(self, level: float) -> None:
        """Set the zoom level.
        
        Args:
            level: Zoom level (1.0 = 100%)
        """
        pass
        
    def fit_to_window(self) -> None:
        """Adjust zoom to fit image to window."""
        pass
