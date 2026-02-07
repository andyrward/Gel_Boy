"""Side panel widget for image properties and lane management."""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox,
    QPushButton, QListWidget
)
from PyQt6.QtCore import pyqtSignal
from gel_boy.gui.widgets.brightness_contrast_widget import BrightnessContrastWidget


class SidePanel(QWidget):
    """Side panel with image properties and lanes list."""
    
    # Forward signals from BrightnessContrastWidget
    min_changed = pyqtSignal(int)
    max_changed = pyqtSignal(int)
    brightness_changed = pyqtSignal(float)  # Emits brightness factor (0.0-2.0)
    contrast_changed = pyqtSignal(float)    # Emits contrast factor (0.0-2.0)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the side panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Lanes section (placeholder)
        lanes_group = QGroupBox("Lanes")
        lanes_layout = QVBoxLayout()
        
        self.lanes_list = QListWidget()
        self.lanes_list.addItem("No lanes defined")
        self.lanes_list.setEnabled(False)
        lanes_layout.addWidget(self.lanes_list)
        
        add_lane_btn = QPushButton("+ Add Lane")
        add_lane_btn.setEnabled(False)
        lanes_layout.addWidget(add_lane_btn)
        
        lanes_group.setLayout(lanes_layout)
        layout.addWidget(lanes_group)
        
        # Brightness/Contrast widget with histogram
        self.brightness_contrast_widget = BrightnessContrastWidget()
        
        # Connect signals
        self.brightness_contrast_widget.min_changed.connect(self.min_changed.emit)
        self.brightness_contrast_widget.max_changed.connect(self.max_changed.emit)
        self.brightness_contrast_widget.brightness_changed.connect(self.brightness_changed.emit)
        self.brightness_contrast_widget.contrast_changed.connect(self.contrast_changed.emit)
        
        layout.addWidget(self.brightness_contrast_widget)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        self.setLayout(layout)
        
    def reset_values(self) -> None:
        """Reset sliders to default values."""
        self.brightness_contrast_widget.reset_values()
        
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable image property controls.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.brightness_contrast_widget.set_enabled(enabled)
        
    def update_histogram(self, image) -> None:
        """Update histogram from image.
        
        Args:
            image: PIL Image to calculate histogram from
        """
        self.brightness_contrast_widget.update_histogram(image)
        
    def get_adjustment_values(self):
        """Get current adjustment values.
        
        Returns:
            Tuple of (min, max, brightness, contrast)
        """
        return self.brightness_contrast_widget.get_values()
    
    def set_bit_depth(self, bit_depth: int, max_value: int) -> None:
        """Set the bit depth for the brightness/contrast widget.
        
        Args:
            bit_depth: Bit depth of the image (8 or 16)
            max_value: Maximum value for the bit depth (255 or 65535)
        """
        self.brightness_contrast_widget.set_bit_depth(bit_depth, max_value)
