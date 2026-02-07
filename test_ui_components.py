#!/usr/bin/env python3
"""
Test script for verifying the enhanced UI components.

This script creates a standalone window to test the BrightnessContrastWidget
and RotateDialog independently. Run this script on a machine with a display
to verify the UI components work correctly.

Usage:
    python3 test_ui_components.py
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt
from PIL import Image
import numpy as np

from gel_boy.gui.widgets.brightness_contrast_widget import BrightnessContrastWidget
from gel_boy.gui.dialogs.rotate_dialog import RotateDialog


class TestWindow(QMainWindow):
    """Test window for UI components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI Components Test")
        self.setMinimumSize(400, 700)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Add BrightnessContrastWidget
        self.bc_widget = BrightnessContrastWidget()
        layout.addWidget(self.bc_widget)
        
        # Add test buttons
        btn_load_gray = QPushButton("Load Test Grayscale Image")
        btn_load_gray.clicked.connect(self.load_grayscale_image)
        layout.addWidget(btn_load_gray)
        
        btn_load_rgb = QPushButton("Load Test RGB Image")
        btn_load_rgb.clicked.connect(self.load_rgb_image)
        layout.addWidget(btn_load_rgb)
        
        btn_rotate = QPushButton("Test Rotation Dialog")
        btn_rotate.clicked.connect(self.test_rotation_dialog)
        layout.addWidget(btn_rotate)
        
        # Connect signals to show feedback
        self.bc_widget.min_changed.connect(
            lambda v: print(f"Min changed: {v}")
        )
        self.bc_widget.max_changed.connect(
            lambda v: print(f"Max changed: {v}")
        )
        self.bc_widget.brightness_changed.connect(
            lambda v: print(f"Brightness changed: {v:.2f}")
        )
        self.bc_widget.contrast_changed.connect(
            lambda v: print(f"Contrast changed: {v:.2f}")
        )
        self.bc_widget.auto_clicked.connect(
            lambda: print("Auto clicked")
        )
        self.bc_widget.reset_clicked.connect(
            lambda: print("Reset clicked")
        )
        
    def load_grayscale_image(self):
        """Load a test grayscale image."""
        # Create gradient image
        array = np.linspace(0, 255, 256 * 256, dtype=np.uint8).reshape(256, 256)
        img = Image.fromarray(array, mode='L')
        self.bc_widget.update_histogram(img)
        print("Loaded grayscale test image")
        
    def load_rgb_image(self):
        """Load a test RGB image."""
        # Create colorful gradient image
        r = np.linspace(0, 255, 256 * 256, dtype=np.uint8).reshape(256, 256)
        g = np.linspace(255, 0, 256 * 256, dtype=np.uint8).reshape(256, 256)
        b = np.full((256, 256), 128, dtype=np.uint8)
        array = np.stack([r, g, b], axis=2)
        img = Image.fromarray(array, mode='RGB')
        self.bc_widget.update_histogram(img)
        print("Loaded RGB test image")
        
    def test_rotation_dialog(self):
        """Test the rotation dialog."""
        result = RotateDialog.get_rotation_parameters(self)
        if result:
            angle, expand, fillcolor = result
            print(f"Rotation parameters: angle={angle}°, expand={expand}, fillcolor={fillcolor}")
        else:
            print("Rotation dialog canceled")


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    print("="*60)
    print("UI Components Test")
    print("="*60)
    print("\nInstructions:")
    print("1. Click 'Load Test Grayscale Image' to see the histogram")
    print("2. Adjust the sliders and observe the visual feedback")
    print("3. Try the Auto button to auto-adjust min/max")
    print("4. Click 'Test Rotation Dialog' to test rotation input")
    print("5. Watch the console for signal output")
    print("="*60)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
