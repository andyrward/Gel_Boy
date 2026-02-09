"""Main application window for Gel_Boy."""

from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFileDialog, QMessageBox, QToolBar, QStatusBar, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from gel_boy.gui.widgets.image_viewer import ImageViewer
from gel_boy.gui.widgets.side_panel import SidePanel
from gel_boy.gui.widgets.intensity_panel import IntensityPanel
from gel_boy.io.image_loader import load_image, get_image_info, get_supported_formats
from gel_boy.core.image_processing import (
    rotate_image, flip_image, invert_image, adjust_brightness, adjust_contrast,
    rotate_image_precise, apply_lut_adjustments
)
from gel_boy.gui.dialogs.rotate_dialog import RotateDialog
from pathlib import Path


class MainWindow(QMainWindow):
    """Main application window for Gel_Boy."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("Gel_Boy - Gel Electrophoresis Analyzer")
        self.setMinimumSize(1200, 800)
        
        self.current_filename: Optional[str] = None
        self.recent_files: list = []
        
        self._setup_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()
        self._connect_signals()
        self._update_actions()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create horizontal splitter for image viewer and side panel
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create image viewer
        self.image_viewer = ImageViewer()
        h_splitter.addWidget(self.image_viewer)
        
        # Create side panel
        self.side_panel = SidePanel()
        h_splitter.addWidget(self.side_panel)
        
        # Set initial sizes (main viewer gets most space)
        h_splitter.setStretchFactor(0, 4)
        h_splitter.setStretchFactor(1, 1)
        
        # Create vertical splitter for main content and bottom panel
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.addWidget(h_splitter)
        
        # Create bottom panel
        self.intensity_panel = IntensityPanel()
        v_splitter.addWidget(self.intensity_panel)
        
        # Set initial sizes (top gets most space)
        v_splitter.setStretchFactor(0, 4)
        v_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(v_splitter)
        central_widget.setLayout(main_layout)
        
    def _create_menus(self) -> None:
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        self.open_action = QAction("&Open Image...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_image)
        file_menu.addAction(self.open_action)
        
        # Recent files submenu (placeholder)
        self.recent_menu = file_menu.addMenu("Recent Files")
        self.recent_menu.setEnabled(False)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setEnabled(False)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setEnabled(False)
        edit_menu.addAction(redo_action)
        
        # Image menu
        image_menu = menubar.addMenu("&Image")
        
        self.rotate_cw_action = QAction("Rotate 90° CW", self)
        self.rotate_cw_action.setShortcut(QKeySequence("Ctrl+R"))
        self.rotate_cw_action.triggered.connect(self.rotate_clockwise)
        image_menu.addAction(self.rotate_cw_action)
        
        self.rotate_ccw_action = QAction("Rotate 90° CCW", self)
        self.rotate_ccw_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        self.rotate_ccw_action.triggered.connect(self.rotate_counterclockwise)
        image_menu.addAction(self.rotate_ccw_action)
        
        self.rotate_180_action = QAction("Rotate 180°", self)
        self.rotate_180_action.triggered.connect(self.rotate_180)
        image_menu.addAction(self.rotate_180_action)
        
        image_menu.addSeparator()
        
        self.rotate_precise_action = QAction("Rotate by Angle...", self)
        self.rotate_precise_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self.rotate_precise_action.triggered.connect(self.rotate_precise)
        image_menu.addAction(self.rotate_precise_action)
        
        image_menu.addSeparator()
        
        self.flip_h_action = QAction("Flip Horizontal", self)
        self.flip_h_action.triggered.connect(self.flip_horizontal)
        image_menu.addAction(self.flip_h_action)
        
        self.flip_v_action = QAction("Flip Vertical", self)
        self.flip_v_action.triggered.connect(self.flip_vertical)
        image_menu.addAction(self.flip_v_action)
        
        image_menu.addSeparator()
        
        self.invert_action = QAction("Invert Colors", self)
        self.invert_action.setShortcut(QKeySequence("Ctrl+I"))
        self.invert_action.triggered.connect(self.invert_colors)
        image_menu.addAction(self.invert_action)
        
        image_menu.addSeparator()
        
        self.reset_action = QAction("Reset to Original", self)
        self.reset_action.setShortcut(QKeySequence("Ctrl+0"))
        self.reset_action.triggered.connect(self.reset_image)
        image_menu.addAction(self.reset_action)
        
        # Analysis menu
        analysis_menu = menubar.addMenu("&Analysis")
        
        detect_lanes_action = QAction("Detect Lanes", self)
        detect_lanes_action.setEnabled(False)
        analysis_menu.addAction(detect_lanes_action)
        
        detect_bands_action = QAction("Detect Bands", self)
        detect_bands_action.setEnabled(False)
        analysis_menu.addAction(detect_bands_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("About Gel_Boy", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def _create_toolbar(self) -> None:
        """Create application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Open button
        open_btn = QAction("Open", self)
        open_btn.setToolTip("Open Image (Ctrl+O)")
        open_btn.triggered.connect(self.open_image)
        toolbar.addAction(open_btn)
        
        toolbar.addSeparator()
        
        # Zoom buttons
        self.zoom_in_action = QAction("Zoom +", self)
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.zoom_in_action.setToolTip("Zoom In (Ctrl++)")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(self.zoom_in_action)
        
        self.zoom_out_action = QAction("Zoom -", self)
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.zoom_out_action.setToolTip("Zoom Out (Ctrl+-)")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(self.zoom_out_action)
        
        self.fit_action = QAction("Fit", self)
        self.fit_action.setToolTip("Fit to Window")
        self.fit_action.triggered.connect(self.fit_to_window)
        toolbar.addAction(self.fit_action)
        
        self.actual_size_action = QAction("100%", self)
        self.actual_size_action.setShortcut(QKeySequence("Ctrl+1"))
        self.actual_size_action.setToolTip("Actual Size (Ctrl+1)")
        self.actual_size_action.triggered.connect(self.actual_size)
        toolbar.addAction(self.actual_size_action)
        
        toolbar.addSeparator()
        
        # Transform buttons
        rotate_cw_btn = QAction("Rotate CW", self)
        rotate_cw_btn.setToolTip("Rotate Clockwise (Ctrl+R)")
        rotate_cw_btn.triggered.connect(self.rotate_clockwise)
        toolbar.addAction(rotate_cw_btn)
        
        rotate_ccw_btn = QAction("Rotate CCW", self)
        rotate_ccw_btn.setToolTip("Rotate Counter-Clockwise (Ctrl+Shift+R)")
        rotate_ccw_btn.triggered.connect(self.rotate_counterclockwise)
        toolbar.addAction(rotate_ccw_btn)
        
        flip_h_btn = QAction("Flip H", self)
        flip_h_btn.setToolTip("Flip Horizontal")
        flip_h_btn.triggered.connect(self.flip_horizontal)
        toolbar.addAction(flip_h_btn)
        
        invert_btn = QAction("Invert", self)
        invert_btn.setToolTip("Invert Colors (Ctrl+I)")
        invert_btn.triggered.connect(self.invert_colors)
        toolbar.addAction(invert_btn)
        
    def _create_status_bar(self) -> None:
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Image info label (left)
        self.image_info_label = QLabel("No image loaded")
        self.status_bar.addWidget(self.image_info_label)
        
        # Zoom level label (right)
        self.zoom_label = QLabel("Zoom: 100%")
        self.status_bar.addPermanentWidget(self.zoom_label)
        
        # Mouse position label (right)
        self.position_label = QLabel("X:--- Y:---")
        self.status_bar.addPermanentWidget(self.position_label)
        
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Image viewer signals
        self.image_viewer.zoom_changed.connect(self._on_zoom_changed)
        self.image_viewer.mouse_moved.connect(self._on_mouse_moved)
        
        # Side panel signals
        self.side_panel.min_changed.connect(self._on_adjustments_changed)
        self.side_panel.max_changed.connect(self._on_adjustments_changed)
        self.side_panel.brightness_changed.connect(self._on_adjustments_changed)
        self.side_panel.contrast_changed.connect(self._on_adjustments_changed)
        
    def _update_actions(self) -> None:
        """Update action enabled states based on whether image is loaded."""
        has_image = self.image_viewer.has_image()
        
        # Enable/disable image-related actions
        self.rotate_cw_action.setEnabled(has_image)
        self.rotate_ccw_action.setEnabled(has_image)
        self.rotate_180_action.setEnabled(has_image)
        self.rotate_precise_action.setEnabled(has_image)
        self.flip_h_action.setEnabled(has_image)
        self.flip_v_action.setEnabled(has_image)
        self.invert_action.setEnabled(has_image)
        self.reset_action.setEnabled(has_image)
        self.zoom_in_action.setEnabled(has_image)
        self.zoom_out_action.setEnabled(has_image)
        self.fit_action.setEnabled(has_image)
        self.actual_size_action.setEnabled(has_image)
        
        # Enable/disable side panel controls
        self.side_panel.set_enabled(has_image)
        
    def open_image(self) -> None:
        """Open an image file."""
        formats = get_supported_formats()
        filter_str = "Image Files (" + " ".join(formats) + ");;All Files (*)"
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Gel Image",
            "",
            filter_str
        )
        
        if filename:
            image = load_image(filename)
            if image:
                self.current_filename = filename
                self.image_viewer.load_image(image)
                self._update_image_info()
                self._update_actions()
                
                # Get bit depth and configure side panel
                from gel_boy.io.image_loader import get_bit_depth
                bit_depth, max_value = get_bit_depth(image)
                self.side_panel.set_bit_depth(bit_depth, max_value)
                
                # Update histogram
                self.side_panel.update_histogram(image)
                
                # Reset side panel sliders
                self.side_panel.reset_values()
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to load image: {filename}"
                )
                
    def _update_image_info(self) -> None:
        """Update status bar with image information."""
        if self.current_filename and self.image_viewer.has_image():
            image = self.image_viewer.get_current_image()
            filename = Path(self.current_filename).name
            self.image_info_label.setText(
                f"{filename} - {image.width}x{image.height}"
            )
        else:
            self.image_info_label.setText("No image loaded")
            
    def _on_zoom_changed(self, level: float) -> None:
        """Handle zoom level change.
        
        Args:
            level: New zoom level
        """
        self.zoom_label.setText(f"Zoom: {int(level * 100)}%")
        
    def _on_mouse_moved(self, x: int, y: int) -> None:
        """Handle mouse movement over image.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.position_label.setText(f"X:{x} Y:{y}")
        
    def _on_adjustments_changed(self, _value=None) -> None:
        """Handle any adjustment slider change (min/max/brightness/contrast).
        
        Uses LUT-based approach for efficient combined adjustments.
        For 16-bit images, also updates the display windowing in the viewer.
        
        Args:
            _value: Slider value (ignored, we get all values from side panel)
        """
        if not self.image_viewer.has_image():
            return
        
        # Get all adjustment values
        min_val, max_val, brightness, contrast = self.side_panel.get_adjustment_values()
        
        # Check if we have a 16-bit image based on current image mode
        current_image = self.image_viewer.current_image
        if current_image and current_image.mode in ('I', 'I;16'):
            # For 16-bit images, update display windowing directly
            # This allows windowing to happen in the viewer for better performance
            self.image_viewer.set_display_range(min_val, max_val)
            
            # Apply brightness/contrast if needed
            if abs(brightness - 1.0) > 0.01 or abs(contrast - 1.0) > 0.01:
                # For brightness/contrast, we need to apply via LUT
                self.image_viewer.apply_transformation(
                    apply_lut_adjustments,
                    min_val,
                    max_val,
                    brightness,
                    contrast
                )
        else:
            # For 8-bit images, apply adjustments cumulatively
            # Apply combined LUT adjustments
            if min_val != 0 or max_val != 255 or abs(brightness - 1.0) > 0.01 or abs(contrast - 1.0) > 0.01:
                self.image_viewer.apply_transformation(
                    apply_lut_adjustments,
                    min_val,
                    max_val,
                    brightness,
                    contrast
                )
            
    def rotate_clockwise(self) -> None:
        """Rotate image 90 degrees clockwise.
        
        Note: PIL's rotate() uses counter-clockwise angles, so we use -90 for CW rotation.
        """
        self.image_viewer.apply_transformation(rotate_image, -90)
        
    def rotate_counterclockwise(self) -> None:
        """Rotate image 90 degrees counter-clockwise.
        
        Note: PIL's rotate() uses counter-clockwise angles, so we use 90 for CCW rotation.
        """
        self.image_viewer.apply_transformation(rotate_image, 90)
        
    def rotate_180(self) -> None:
        """Rotate image 180 degrees."""
        self.image_viewer.apply_transformation(rotate_image, 180)
        
    def rotate_precise(self) -> None:
        """Rotate image by precise angle using dialog."""
        result = RotateDialog.get_rotation_parameters(self)
        if result is not None:
            angle, expand, fillcolor = result
            
            # Convert color name to RGB tuple
            if fillcolor == "white":
                color = (255, 255, 255)
            else:
                color = (0, 0, 0)
            
            # Apply rotation
            self.image_viewer.apply_transformation(
                rotate_image_precise,
                angle,
                expand,
                color
            )
            
            # Update histogram after transformation
            current_image = self.image_viewer.get_current_image()
            if current_image:
                self.side_panel.update_histogram(current_image)
        
    def flip_horizontal(self) -> None:
        """Flip image horizontally."""
        self.image_viewer.apply_transformation(flip_image, True)
        
    def flip_vertical(self) -> None:
        """Flip image vertically."""
        self.image_viewer.apply_transformation(flip_image, False)
        
    def invert_colors(self) -> None:
        """Invert image colors."""
        self.image_viewer.apply_transformation(invert_image)
        
    def reset_image(self) -> None:
        """Reset image to original."""
        self.image_viewer.reset_image()
        self.side_panel.reset_values()
        
    def zoom_in(self) -> None:
        """Zoom in."""
        self.image_viewer.zoom_in()
        
    def zoom_out(self) -> None:
        """Zoom out."""
        self.image_viewer.zoom_out()
        
    def fit_to_window(self) -> None:
        """Fit image to window."""
        self.image_viewer.fit_to_window()
        
    def actual_size(self) -> None:
        """Set zoom to 100%."""
        self.image_viewer.actual_size()
        
    def show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Gel_Boy",
            "<h2>Gel_Boy</h2>"
            "<p>Version 0.1.0</p>"
            "<p>A cross-platform gel electrophoresis image analysis "
            "and annotation tool.</p>"
            "<p>Built with Python and PyQt6</p>"
        )
