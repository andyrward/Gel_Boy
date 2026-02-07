"""Brightness/Contrast widget with histogram display (ImageJ-style)."""

from typing import Optional, Tuple
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PIL import Image


class BrightnessContrastWidget(QWidget):
    """Widget for brightness/contrast adjustment with live histogram.
    
    Features ImageJ-style controls including:
    - Histogram display with intensity distribution
    - Min/Max sliders for intensity windowing
    - Brightness/Contrast sliders
    - Visual feedback on histogram
    - Auto and Reset buttons
    """
    
    # Signals
    min_changed = pyqtSignal(int)  # Emits minimum value (0-255)
    max_changed = pyqtSignal(int)  # Emits maximum value (0-255)
    brightness_changed = pyqtSignal(float)  # Emits brightness factor (0.0-2.0)
    contrast_changed = pyqtSignal(float)  # Emits contrast factor (0.0-2.0)
    auto_clicked = pyqtSignal()  # Emitted when Auto button clicked
    reset_clicked = pyqtSignal()  # Emitted when Reset button clicked
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the brightness/contrast widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Cached histogram data
        self._histogram_bins: Optional[np.ndarray] = None
        self._histogram_values: Optional[np.ndarray] = None
        self._updating = False  # Flag to prevent signal loops
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Histogram display
        self.figure = Figure(figsize=(4, 2), dpi=75)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(150)
        self.canvas.setMaximumHeight(200)
        self.ax = self.figure.add_subplot(111)
        self.figure.tight_layout()
        
        # Initialize empty histogram
        self.ax.set_xlim(0, 255)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel('Intensity', fontsize=8)
        self.ax.set_ylabel('Count', fontsize=8)
        self.ax.tick_params(labelsize=7)
        self.ax.grid(True, alpha=0.3)
        
        # Store line references for updates
        self.hist_line = None
        self.min_line = None
        self.max_line = None
        self.filled_region = None
        
        layout.addWidget(self.canvas)
        
        # Min/Max controls group
        window_group = QGroupBox("Intensity Window")
        window_layout = QVBoxLayout()
        
        # Minimum slider
        min_label = QLabel("Minimum:")
        window_layout.addWidget(min_label)
        
        min_container = QHBoxLayout()
        self.min_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_slider.setMinimum(0)
        self.min_slider.setMaximum(255)
        self.min_slider.setValue(0)
        self.min_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.min_slider.setTickInterval(32)
        self.min_slider.valueChanged.connect(self._on_min_changed)
        min_container.addWidget(self.min_slider)
        
        self.min_value = QLabel("0")
        self.min_value.setMinimumWidth(35)
        min_container.addWidget(self.min_value)
        
        window_layout.addLayout(min_container)
        
        # Maximum slider
        max_label = QLabel("Maximum:")
        window_layout.addWidget(max_label)
        
        max_container = QHBoxLayout()
        self.max_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_slider.setMinimum(0)
        self.max_slider.setMaximum(255)
        self.max_slider.setValue(255)
        self.max_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.max_slider.setTickInterval(32)
        self.max_slider.valueChanged.connect(self._on_max_changed)
        max_container.addWidget(self.max_slider)
        
        self.max_value = QLabel("255")
        self.max_value.setMinimumWidth(35)
        max_container.addWidget(self.max_value)
        
        window_layout.addLayout(max_container)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        # Brightness/Contrast controls group
        adjust_group = QGroupBox("Brightness & Contrast")
        adjust_layout = QVBoxLayout()
        
        # Brightness control
        brightness_label = QLabel("Brightness:")
        adjust_layout.addWidget(brightness_label)
        
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
        
        adjust_layout.addLayout(brightness_container)
        
        # Contrast control
        contrast_label = QLabel("Contrast:")
        adjust_layout.addWidget(contrast_label)
        
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
        
        adjust_layout.addLayout(contrast_container)
        
        adjust_group.setLayout(adjust_layout)
        layout.addWidget(adjust_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.auto_btn = QPushButton("Auto")
        self.auto_btn.setToolTip("Auto-adjust min/max based on histogram")
        self.auto_btn.clicked.connect(self._on_auto_clicked)
        buttons_layout.addWidget(self.auto_btn)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setToolTip("Reset all controls to default values")
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        buttons_layout.addWidget(self.reset_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
    def _on_min_changed(self, value: int) -> None:
        """Handle minimum slider change.
        
        Args:
            value: Slider value (0-255)
        """
        if self._updating:
            return
            
        # Ensure min < max
        max_val = self.max_slider.value()
        if value >= max_val:
            self._updating = True
            self.min_slider.setValue(max_val - 1)
            self._updating = False
            return
            
        self.min_value.setText(str(value))
        self._update_histogram_markers()
        self.min_changed.emit(value)
        
    def _on_max_changed(self, value: int) -> None:
        """Handle maximum slider change.
        
        Args:
            value: Slider value (0-255)
        """
        if self._updating:
            return
            
        # Ensure max > min
        min_val = self.min_slider.value()
        if value <= min_val:
            self._updating = True
            self.max_slider.setValue(min_val + 1)
            self._updating = False
            return
            
        self.max_value.setText(str(value))
        self._update_histogram_markers()
        self.max_changed.emit(value)
        
    def _on_brightness_changed(self, value: int) -> None:
        """Handle brightness slider change.
        
        Args:
            value: Slider value (0-200)
        """
        self.brightness_value.setText(f"{value}%")
        factor = value / 100.0
        self.brightness_changed.emit(factor)
        
    def _on_contrast_changed(self, value: int) -> None:
        """Handle contrast slider change.
        
        Args:
            value: Slider value (0-200)
        """
        self.contrast_value.setText(f"{value}%")
        factor = value / 100.0
        self.contrast_changed.emit(factor)
        
    def _on_auto_clicked(self) -> None:
        """Handle Auto button click."""
        if self._histogram_values is not None:
            # Calculate auto levels based on histogram
            # Find 1st and 99th percentile for robust auto-leveling
            cumsum = np.cumsum(self._histogram_values)
            total = cumsum[-1]
            
            if total > 0:
                min_idx = np.searchsorted(cumsum, total * 0.01)
                max_idx = np.searchsorted(cumsum, total * 0.99)
                
                self._updating = True
                self.min_slider.setValue(int(min_idx))
                self.max_slider.setValue(int(max_idx))
                self._updating = False
                
                self._update_histogram_markers()
                self.min_changed.emit(int(min_idx))
                self.max_changed.emit(int(max_idx))
        
        self.auto_clicked.emit()
        
    def _on_reset_clicked(self) -> None:
        """Handle Reset button click."""
        self._updating = True
        self.min_slider.setValue(0)
        self.max_slider.setValue(255)
        self.brightness_slider.setValue(100)
        self.contrast_slider.setValue(100)
        self._updating = False
        
        self._update_histogram_markers()
        self.reset_clicked.emit()
        
    def update_histogram(self, image: Optional[Image.Image]) -> None:
        """Update histogram from image.
        
        Args:
            image: PIL Image to calculate histogram from
        """
        if image is None:
            self._histogram_bins = None
            self._histogram_values = None
            self._clear_histogram()
            return
        
        # Calculate histogram
        from gel_boy.core.image_processing import calculate_histogram
        bins, values = calculate_histogram(image)
        
        self._histogram_bins = bins
        self._histogram_values = values
        
        # Update display
        self._draw_histogram()
        
    def _draw_histogram(self) -> None:
        """Draw the histogram on the canvas."""
        if self._histogram_bins is None or self._histogram_values is None:
            return
        
        self.ax.clear()
        
        # Plot histogram
        self.ax.fill_between(
            self._histogram_bins,
            self._histogram_values,
            alpha=0.7,
            color='steelblue',
            label='Intensity Distribution'
        )
        
        # Set limits
        self.ax.set_xlim(0, 255)
        max_count = np.max(self._histogram_values) if len(self._histogram_values) > 0 else 100
        self.ax.set_ylim(0, max_count * 1.1)
        
        # Labels and grid
        self.ax.set_xlabel('Intensity', fontsize=8)
        self.ax.set_ylabel('Count', fontsize=8)
        self.ax.tick_params(labelsize=7)
        self.ax.grid(True, alpha=0.3)
        
        # Add min/max markers
        self._update_histogram_markers()
        
        self.canvas.draw()
        
    def _update_histogram_markers(self) -> None:
        """Update min/max markers on histogram."""
        if self._histogram_bins is None:
            return
        
        min_val = self.min_slider.value()
        max_val = self.max_slider.value()
        
        # Remove old lines if they exist
        if hasattr(self, 'min_line') and self.min_line:
            try:
                self.min_line.remove()
            except ValueError:
                pass
        if hasattr(self, 'max_line') and self.max_line:
            try:
                self.max_line.remove()
            except ValueError:
                pass
        if hasattr(self, 'filled_region') and self.filled_region:
            try:
                self.filled_region.remove()
            except ValueError:
                pass
        
        # Draw shaded region between min and max
        ylim = self.ax.get_ylim()
        self.filled_region = self.ax.axvspan(
            min_val, max_val,
            alpha=0.2,
            color='green',
            label='Active Range'
        )
        
        # Draw vertical lines at min and max
        self.min_line = self.ax.axvline(
            min_val,
            color='red',
            linestyle='--',
            linewidth=1.5,
            label=f'Min: {min_val}'
        )
        self.max_line = self.ax.axvline(
            max_val,
            color='blue',
            linestyle='--',
            linewidth=1.5,
            label=f'Max: {max_val}'
        )
        
        self.canvas.draw()
        
    def _clear_histogram(self) -> None:
        """Clear the histogram display."""
        self.ax.clear()
        self.ax.set_xlim(0, 255)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel('Intensity', fontsize=8)
        self.ax.set_ylabel('Count', fontsize=8)
        self.ax.tick_params(labelsize=7)
        self.ax.grid(True, alpha=0.3)
        self.ax.text(
            127.5, 50,
            'No Image',
            ha='center',
            va='center',
            fontsize=12,
            color='gray'
        )
        self.canvas.draw()
        
    def reset_values(self) -> None:
        """Reset all sliders to default values."""
        self._on_reset_clicked()
        
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all controls.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.min_slider.setEnabled(enabled)
        self.max_slider.setEnabled(enabled)
        self.brightness_slider.setEnabled(enabled)
        self.contrast_slider.setEnabled(enabled)
        self.auto_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
        
    def get_values(self) -> Tuple[int, int, float, float]:
        """Get current slider values.
        
        Returns:
            Tuple of (min, max, brightness, contrast)
        """
        return (
            self.min_slider.value(),
            self.max_slider.value(),
            self.brightness_slider.value() / 100.0,
            self.contrast_slider.value() / 100.0
        )
