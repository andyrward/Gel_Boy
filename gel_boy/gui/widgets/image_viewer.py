"""Custom image display widget for gel electrophoresis images."""

from typing import Optional
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QRubberBand
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRect, QPoint, QSize
from PyQt6.QtGui import QPixmap, QPainter, QImage, QWheelEvent, QMouseEvent, QCursor
from PIL import Image
import numpy as np

# Viewer interaction modes
MODE_CROP = "crop"


class ImageViewer(QGraphicsView):
    """Custom widget for displaying and interacting with gel images.

    Provides zoom, pan, and annotation capabilities for gel electrophoresis images.
    """

    image_clicked = pyqtSignal(int, int)  # Emits x, y coordinates
    zoom_changed = pyqtSignal(float)  # Emits zoom level
    mouse_moved = pyqtSignal(int, int)  # Emits mouse position on image
    crop_selected = pyqtSignal(int, int, int, int)  # x, y, width, height in image coords

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
        
        # Display parameters for 16-bit windowing
        self.display_min: int = 0
        self.display_max: int = 255

        # Track mouse for position display
        self.setMouseTracking(True)

        # Lane overlay (initially hidden)
        self._lane_overlay: Optional['LaneOverlay'] = None

        # Crop mode state
        self._crop_mode: bool = False
        self._crop_start: Optional[QPoint] = None
        self._crop_rubber_band: Optional[QRubberBand] = None

    def load_image(self, image: Image.Image) -> None:
        """Load an image into the viewer.

        Args:
            image: PIL Image to display
        """
        self.original_image = image.copy()
        self.current_image = image.copy()
        
        # Set default display range based on bit depth
        from gel_boy.io.image_loader import get_bit_depth
        _, max_val = get_bit_depth(image)
        self.display_min = 0
        self.display_max = max_val
        
        self.update_display()
        self.fit_to_window()

    def update_display(self) -> None:
        """Update the displayed image.
        
        For 16-bit images, applies windowing to convert to 8-bit for display.
        """
        if self.current_image is None:
            return

        try:
            img = self.current_image

            # Validate image dimensions
            if img.width <= 0 or img.height <= 0:
                raise ValueError(
                    f"Invalid image dimensions: {img.width}x{img.height}"
                )

            qimage = self._pil_to_qimage(img)

            if qimage is None or qimage.isNull():
                raise RuntimeError(
                    f"QImage conversion produced a null image "
                    f"(mode={img.mode}, size={img.size})"
                )

        except Exception as exc:
            print(f"[ImageViewer] update_display error: {exc}")
            # Attempt a safe fallback: convert to RGB and retry once
            try:
                fallback = self.current_image.convert("RGB")
                qimage = self._pil_to_qimage(fallback)
                if qimage is None or qimage.isNull():
                    print("[ImageViewer] Fallback RGB conversion also failed – "
                          "display not updated.")
                    return
            except Exception as exc2:
                print(f"[ImageViewer] Fallback conversion failed: {exc2}")
                return

        pixmap = QPixmap.fromImage(qimage)

        if pixmap.isNull():
            print("[ImageViewer] QPixmap.fromImage returned a null pixmap – "
                  "display not updated.")
            return

        # Update or create pixmap item
        if self.pixmap_item is None:
            self.pixmap_item = self.scene.addPixmap(pixmap)
        else:
            self.pixmap_item.setPixmap(pixmap)

        self.scene.setSceneRect(self.pixmap_item.boundingRect())
        self._update_overlay_transform()

    def _pil_to_qimage(self, img: Image.Image) -> Optional[QImage]:
        """Convert a PIL Image to a QImage.

        Returns a deep-copied QImage that owns its data, or ``None`` on
        failure.
        """
        mode = img.mode

        # Handle 16-bit images with windowing
        if mode in ('I', 'I;16'):
            data = np.array(img, dtype=np.float32)

            # Apply windowing: map [display_min, display_max] to [0, 255]
            data = np.clip(data, self.display_min, self.display_max)
            if self.display_max > self.display_min:
                data = (
                    (data - self.display_min)
                    / (self.display_max - self.display_min)
                    * 255
                )
            data = data.astype(np.uint8)

            # Keep bytes in a named variable so they are not GC'd before
            # QImage makes its own copy of the data.
            raw_bytes = data.tobytes()
            qimage = QImage(
                raw_bytes,
                data.shape[1],
                data.shape[0],
                data.shape[1],
                QImage.Format.Format_Grayscale8,
            )

        elif mode == "RGB":
            raw_bytes = img.tobytes("raw", "RGB")
            qimage = QImage(
                raw_bytes,
                img.width,
                img.height,
                img.width * 3,
                QImage.Format.Format_RGB888,
            )

        elif mode == "L":
            raw_bytes = img.tobytes("raw", "L")
            qimage = QImage(
                raw_bytes,
                img.width,
                img.height,
                img.width,
                QImage.Format.Format_Grayscale8,
            )

        elif mode == "RGBA":
            raw_bytes = img.tobytes("raw", "RGBA")
            qimage = QImage(
                raw_bytes,
                img.width,
                img.height,
                img.width * 4,
                QImage.Format.Format_RGBA8888,
            )

        else:
            # Convert to RGB for all other modes
            img_rgb = img.convert("RGB")
            raw_bytes = img_rgb.tobytes("raw", "RGB")
            qimage = QImage(
                raw_bytes,
                img_rgb.width,
                img_rgb.height,
                img_rgb.width * 3,
                QImage.Format.Format_RGB888,
            )

        return qimage.copy()  # Deep copy so QImage owns its data

    def set_zoom(self, level: float) -> None:
        """Set the zoom level.

        Args:
            level: Zoom level (1.0 = 100%)
        """
        self.zoom_level = level
        self.resetTransform()
        self.scale(level, level)
        self.zoom_changed.emit(level)
        self._update_overlay_transform()

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
        """Handle mouse move to emit position and update crop rubber band.

        Args:
            event: Mouse event
        """
        if self._crop_mode and self._crop_start is not None:
            # Update rubber band selection
            if self._crop_rubber_band is not None:
                self._crop_rubber_band.setGeometry(
                    QRect(self._crop_start, event.pos()).normalized()
                )
        else:
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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press to start crop selection.

        Args:
            event: Mouse event
        """
        if self._crop_mode and event.button() == Qt.MouseButton.LeftButton:
            self._crop_start = event.pos()
            if self._crop_rubber_band is None:
                self._crop_rubber_band = QRubberBand(
                    QRubberBand.Shape.Rectangle, self.viewport()
                )
            self._crop_rubber_band.setGeometry(QRect(self._crop_start, QSize()))
            self._crop_rubber_band.show()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release to finalise crop selection.

        Args:
            event: Mouse event
        """
        if (
            self._crop_mode
            and self._crop_start is not None
            and event.button() == Qt.MouseButton.LeftButton
        ):
            rect = QRect(self._crop_start, event.pos()).normalized()
            if self._crop_rubber_band is not None:
                self._crop_rubber_band.hide()
            self._crop_start = None

            # Convert viewport rectangle to image coordinates
            scene_tl = self.mapToScene(rect.topLeft())
            scene_br = self.mapToScene(rect.bottomRight())

            x = int(scene_tl.x())
            y = int(scene_tl.y())
            w = int(scene_br.x() - scene_tl.x())
            h = int(scene_br.y() - scene_tl.y())

            if w >= 10 and h >= 10:
                self.crop_selected.emit(x, y, w, h)
        else:
            super().mouseReleaseEvent(event)

    def set_crop_mode(self, enabled: bool) -> None:
        """Enable or disable crop selection mode.

        In crop mode the normal scroll-hand drag is disabled and the cursor
        changes to a crosshair so the user can drag out a crop rectangle.

        Args:
            enabled: ``True`` to enter crop mode, ``False`` to leave it.
        """
        self._crop_mode = enabled
        if enabled:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.unsetCursor()
            # Hide rubber band if visible
            if self._crop_rubber_band is not None:
                self._crop_rubber_band.hide()
            self._crop_start = None

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
            # Reset display range to full range
            from gel_boy.io.image_loader import get_bit_depth
            _, max_val = get_bit_depth(self.original_image)
            self.display_min = 0
            self.display_max = max_val
            self.update_display()
    
    def set_display_range(self, min_val: int, max_val: int) -> None:
        """Set the display range for windowing (used for 16-bit images).
        
        Args:
            min_val: Minimum value to map to black
            max_val: Maximum value to map to white
        """
        self.display_min = min_val
        self.display_max = max_val
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

    def get_lane_overlay(self) -> 'LaneOverlay':
        """Get the lane overlay widget, creating it if needed.

        Returns:
            The LaneOverlay widget
        """
        if self._lane_overlay is None:
            from gel_boy.gui.widgets.lane_overlay import LaneOverlay
            self._lane_overlay = LaneOverlay(self.viewport())
            self._lane_overlay.resize(self.viewport().size())
            self._update_overlay_transform()
        return self._lane_overlay

    def set_lane_overlay_visible(self, visible: bool) -> None:
        """Show or hide the lane overlay.

        Args:
            visible: True to show overlay
        """
        overlay = self.get_lane_overlay()
        overlay.setVisible(visible)
        if visible:
            # Ensure the overlay is on top of all other viewport children so
            # that it receives mouse events correctly.
            overlay.raise_()

    def set_lane_drag_mode(self, drawing_active: bool) -> None:
        """Enable or disable panning while lane draw/edit mode is active.

        When the lane overlay is in DRAW or EDIT mode the scroll-hand drag must
        be disabled so that mouse events reach the overlay instead of panning
        the view.  Mirrors the behaviour of :meth:`set_crop_mode`.

        Args:
            drawing_active: ``True`` when entering draw/edit mode (disables
                panning), ``False`` when returning to view mode (re-enables
                panning).
        """
        if drawing_active:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
            # Ensure the overlay is raised so it receives mouse events
            if self._lane_overlay is not None:
                self._lane_overlay.raise_()
        else:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.unsetCursor()

    def _update_overlay_transform(self) -> None:
        """Update the overlay's coordinate transform to match current zoom/pan."""
        if self._lane_overlay is None or self.pixmap_item is None:
            return

        # Map the image top-left corner to viewport coordinates
        scene_rect = self.pixmap_item.boundingRect()
        top_left_scene = scene_rect.topLeft()
        top_left_view = self.mapFromScene(top_left_scene)

        # Map a unit pixel in image space to viewport pixels
        one_px_right = self.mapFromScene(top_left_scene.x() + 1, top_left_scene.y())
        one_px_down = self.mapFromScene(top_left_scene.x(), top_left_scene.y() + 1)

        scale_x = one_px_right.x() - top_left_view.x()
        scale_y = one_px_down.y() - top_left_view.y()

        self._lane_overlay.set_transform(
            1.0 / scale_x if scale_x != 0 else 1.0,
            1.0 / scale_y if scale_y != 0 else 1.0,
            float(top_left_view.x()),
            float(top_left_view.y()),
        )

    def resizeEvent(self, event) -> None:
        """Handle resize to keep overlay in sync."""
        super().resizeEvent(event)
        if self._lane_overlay is not None:
            self._lane_overlay.resize(self.viewport().size())
            self._update_overlay_transform()
