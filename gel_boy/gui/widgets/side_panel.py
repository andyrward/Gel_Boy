"""Side panel widget for image properties and lane management."""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QSlider, QLabel, 
    QPushButton, QListWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal


class SidePanel(QWidget):
    """Side panel with image properties and lanes list."""
    
    brightness_changed = pyqtSignal(float)  # Emits brightness factor (0.0-2.0)
    contrast_changed = pyqtSignal(float)    # Emits contrast factor (0.0-2.0)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the side panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.setMaximumWidth(300)
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
        
        # Image properties section
        props_group = QGroupBox("Image Properties")
        props_layout = QVBoxLayout()
        
        # Brightness control
        brightness_label = QLabel("Brightness:")
        props_layout.addWidget(brightness_label)
        
        brightness_container = QHBoxLayout()
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(200)
        self.brightness_slider.setValue(100)
        self.brightness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.brightness_slider.setTickInterval(25)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        brightness_container.addWidget(self.brightness_slider)
        
        self.brightness_value = QLabel("100%")
        self.brightness_value.setMinimumWidth(50)
        brightness_container.addWidget(self.brightness_value)
        
        props_layout.addLayout(brightness_container)
        
        # Contrast control
        contrast_label = QLabel("Contrast:")
        props_layout.addWidget(contrast_label)
        
        contrast_container = QHBoxLayout()
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.contrast_slider.setTickInterval(25)
        self.contrast_slider.valueChanged.connect(self._on_contrast_changed)
        contrast_container.addWidget(self.contrast_slider)
        
        self.contrast_value = QLabel("100%")
        self.contrast_value.setMinimumWidth(50)
        contrast_container.addWidget(self.contrast_value)
        
        props_layout.addLayout(contrast_container)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_values)
        props_layout.addWidget(self.reset_btn)
        
        props_group.setLayout(props_layout)
        layout.addWidget(props_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        self.setLayout(layout)
        
    def _on_brightness_changed(self, value: int) -> None:
        """Handle brightness slider change.
        
        Args:
            value: Slider value (0-200)
        """
        self.brightness_value.setText(f"{value}%")
        # Convert to factor (0.0-2.0)
        factor = value / 100.0
        self.brightness_changed.emit(factor)
        
    def _on_contrast_changed(self, value: int) -> None:
        """Handle contrast slider change.
        
        Args:
            value: Slider value (0-200)
        """
        self.contrast_value.setText(f"{value}%")
        # Convert to factor (0.0-2.0)
        factor = value / 100.0
        self.contrast_changed.emit(factor)
        
    def reset_values(self) -> None:
        """Reset sliders to default values."""
        self.brightness_slider.setValue(100)
        self.contrast_slider.setValue(100)
        
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable image property controls.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.brightness_slider.setEnabled(enabled)
        self.contrast_slider.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
