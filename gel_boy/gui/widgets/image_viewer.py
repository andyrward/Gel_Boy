"""Custom image display widget for gel electrophoresis images."""

from typing import Optional
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPixmap, QPainter, QImage, QWheelEvent, QMouseEvent
from PIL import Image
import numpy as np


class ImageViewer(QGraphicsView):
    """Custom widget for displaying and interacting with gel images.

    Provides zoom, pan, and annotation capabilities for gel electrophoresis images.
    """

    image_clicked = pyqtSignal(int, int)  # Emits x, y coordinates
    zoom_changed = pyqtSignal(float)  # Emits zoom level
    mouse_moved = pyqtSignal(int, int)  # Emits mouse position on image

    def __init__(self, parent: Optional[QGraphicsView] = None):
        """Initialize the image viewer.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Setup scene
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Enable smooth transformations
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Enable drag to pan
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Store images
        self.original_image: Optional[Image.Image] = None
        self.current_image: Optional[Image.Image] = None
        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.zoom_level: float = 1.0

        # Track mouse for position display
        self.setMouseTracking(True)

    def load_image(self, image: Image.Image) -> None:
        """Load an image into the viewer.

        Args:
            image: PIL Image to display
        """
        self.original_image = image.copy()
        self.current_image = image.copy()
        self.update_display()
        self.fit_to_window()

    def update_display(self) -> None:
        """Update the displayed image."""
        if self.current_image is None:
            return

        # Convert PIL Image to QPixmap
        if self.current_image.mode == "RGB":
            data = self.current_image.tobytes("raw", "RGB")
            qimage = QImage(
                data,
                self.current_image.width,
                self.current_image.height,
                self.current_image.width * 3,
                QImage.Format.Format_RGB888,
            )
            qimage = qimage.copy()  # Make a deep copy to own the data
        elif self.current_image.mode == "L":
            data = self.current_image.tobytes("raw", "L")
            qimage = QImage(
                data,
                self.current_image.width,
                self.current_image.height,
                self.current_image.width,
                QImage.Format.Format_Grayscale8,
            )
            qimage = qimage.copy()  # Make a deep copy to own the data
        else:
            # Convert to RGB if other format
            img_rgb = self.current_image.convert("RGB")
            data = img_rgb.tobytes("raw", "RGB")
            qimage = QImage(
                data,
                img_rgb.width,
                img_rgb.height,
                img_rgb.width * 3,
                QImage.Format.Format_RGB888,
            )
            qimage = qimage.copy()  # Make a deep copy to own the data

        pixmap = QPixmap.fromImage(qimage)

        # Update or create pixmap item
        if self.pixmap_item is None:
            self.pixmap_item = self.scene.addPixmap(pixmap)
        else:
            self.pixmap_item.setPixmap(pixmap)

        self.scene.setSceneRect(self.pixmap_item.boundingRect())

    def set_zoom(self, level: float) -> None:
        """Set the zoom level.

        Args:
            level: Zoom level (1.0 = 100%)
        """
        self.zoom_level = level
        self.resetTransform()
        self.scale(level, level)
        self.zoom_changed.emit(level)

    def zoom_in(self) -> None:
        """Zoom in by 25%."""
        self.set_zoom(self.zoom_level * 1.25)

    def zoom_out(self) -> None:
        """Zoom out by 25%."""
        self.set_zoom(self.zoom_level / 1.25)

    def fit_to_window(self) -> None:
        """Adjust zoom to fit image to window."""
        if self.pixmap_item is None:
            return

        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        # Calculate actual zoom level
        transform = self.transform()
        self.zoom_level = transform.m11()
        self.zoom_changed.emit(self.zoom_level)

    def actual_size(self) -> None:
        """Set zoom to 100% (actual size)."""
        self.set_zoom(1.0)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming.

        Args:
            event: Wheel event
        """
        if self.pixmap_item is None:
            return

        # Zoom with mouse wheel
        factor = 1.15
        if event.angleDelta().y() > 0:
            # Zoom in
            self.set_zoom(self.zoom_level * factor)
        else:
            # Zoom out
            self.set_zoom(self.zoom_level / factor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move to emit position.

        Args:
            event: Mouse event
        """
        super().mouseMoveEvent(event)

        if self.pixmap_item is None:
            return

        # Get position in scene coordinates
        scene_pos = self.mapToScene(event.pos())

        # Check if position is within image bounds
        if self.pixmap_item.contains(scene_pos):
            x = int(scene_pos.x())
            y = int(scene_pos.y())
            self.mouse_moved.emit(x, y)

    def apply_transformation(self, transform_func, *args) -> None:
        """Apply transformation to current image (non-destructive).

        Args:
            transform_func: Function to apply to image (takes Image.Image, returns Image.Image)
            *args: Arguments to pass to transform function
        """
        if self.current_image is None:
            return

        self.current_image = transform_func(self.current_image, *args)
        self.update_display()

    def reset_image(self) -> None:
        """Reset to original image, removing all transformations."""
        if self.original_image:
            self.current_image = self.original_image.copy()
            self.update_display()

    def get_current_image(self) -> Optional[Image.Image]:
        """Get the current (transformed) image.

        Returns:
            Current PIL Image or None
        """
        return self.current_image

    def has_image(self) -> bool:
        """Check if an image is loaded.

        Returns:
            True if image is loaded, False otherwise
        """
        return self.original_image is not None
