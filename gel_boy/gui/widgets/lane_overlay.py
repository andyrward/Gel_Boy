"""Lane overlay widget for drawing and editing lanes on gel images."""

from typing import Optional, List, Tuple
from PyQt6.QtWidgets import (
    QWidget, QMenu, QDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QLineEdit,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QMouseEvent,
    QPaintEvent
)
from gel_boy.models.lane import Lane


# Drawing mode constants
MODE_VIEW = "view"
MODE_DRAW = "draw"
MODE_EDIT = "edit"

# Handle size in pixels for edge dragging
HANDLE_SIZE = 8

# Color palette for auto-assigned lane colors (cycles with modulo)
_LANE_COLOR_PALETTE = [
    (0, 120, 215), (0, 183, 74), (234, 67, 53), (255, 164, 0),
    (138, 43, 226), (255, 105, 180), (0, 206, 209), (139, 69, 19),
]


class LaneOverlay(QWidget):
    """Transparent overlay widget for interactive lane drawing and editing.

    Draws lanes as colored rectangles on top of the image viewer.
    Supports:
    - Click-and-drag to create new lanes
    - Dragging lane edges to resize
    - Dragging entire lane to reposition
    - Right-click context menu for delete/edit
    - Hover effects and visual handles

    Signals:
        lane_added(Lane): Emitted when a new lane is drawn
        lane_removed(int): Emitted with lane index when a lane is deleted
        lane_modified(int, Lane): Emitted when a lane is modified
        lane_selected(int): Emitted with lane index when a lane is selected
    """

    lane_added = pyqtSignal(object)       # Lane object
    lane_removed = pyqtSignal(int)        # Lane index
    lane_modified = pyqtSignal(int, object)  # (index, Lane)
    lane_selected = pyqtSignal(int)       # Lane index

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the lane overlay.

        Args:
            parent: Parent widget (typically the ImageViewer)
        """
        super().__init__(parent)

        # Make the widget transparent so the image shows through
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setMouseTracking(True)

        self.lanes: List[Lane] = []
        self.mode: str = MODE_VIEW

        # Drawing state
        self._drawing = False
        self._draw_start: Optional[QPoint] = None
        self._draw_current: Optional[QPoint] = None

        # Editing state
        self._selected_lane_idx: int = -1
        self._hovered_lane_idx: int = -1
        self._drag_mode: Optional[str] = None  # 'move', 'left_edge', 'right_edge'
        self._drag_start: Optional[QPoint] = None
        self._drag_lane_original: Optional[Tuple] = None  # (x_start, x_end, y_start, y_end)

        # Scale factor to map overlay coords -> image coords
        self._scale_x: float = 1.0
        self._scale_y: float = 1.0
        self._offset_x: float = 0.0
        self._offset_y: float = 0.0

    def set_mode(self, mode: str) -> None:
        """Set the interaction mode.

        Args:
            mode: One of MODE_VIEW, MODE_DRAW, or MODE_EDIT
        """
        self.mode = mode
        self._drawing = False
        self._draw_start = None
        self._draw_current = None

        if mode == MODE_DRAW:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif mode == MODE_EDIT:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        self.update()

    def set_transform(
        self,
        scale_x: float,
        scale_y: float,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> None:
        """Set the coordinate transform from overlay coords to image coords.

        Args:
            scale_x: Horizontal scale factor (image_width / overlay_width)
            scale_y: Vertical scale factor (image_height / overlay_height)
            offset_x: Horizontal offset in overlay pixels
            offset_y: Vertical offset in overlay pixels
        """
        self._scale_x = scale_x if scale_x > 0 else 1.0
        self._scale_y = scale_y if scale_y > 0 else 1.0
        self._offset_x = offset_x
        self._offset_y = offset_y

    def set_lanes(self, lanes: List[Lane]) -> None:
        """Set the list of lanes to display.

        Args:
            lanes: List of Lane objects to display
        """
        self.lanes = lanes
        self._selected_lane_idx = -1
        self.update()

    def get_lanes(self) -> List[Lane]:
        """Get the current list of lanes.

        Returns:
            List of Lane objects
        """
        return self.lanes

    def clear_lanes(self) -> None:
        """Remove all lanes."""
        self.lanes = []
        self._selected_lane_idx = -1
        self.update()

    def select_lane(self, index: int) -> None:
        """Select a lane by index.

        Args:
            index: Lane index to select (-1 to deselect)
        """
        self._selected_lane_idx = index
        self.update()

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def _overlay_to_image(self, point: QPoint) -> Tuple[int, int]:
        """Convert overlay coordinates to image coordinates."""
        ix = int((point.x() - self._offset_x) * self._scale_x)
        iy = int((point.y() - self._offset_y) * self._scale_y)
        return ix, iy

    def _image_to_overlay(self, ix: float, iy: float) -> Tuple[float, float]:
        """Convert image coordinates to overlay coordinates."""
        ox = ix / self._scale_x + self._offset_x
        oy = iy / self._scale_y + self._offset_y
        return ox, oy

    def _lane_rect_overlay(self, lane: Lane) -> QRect:
        """Get the lane rectangle in overlay (screen) coordinates."""
        ox1, oy1 = self._image_to_overlay(lane.x_start, lane.y_start)
        ox2, oy2 = self._image_to_overlay(lane.x_end, lane.y_end)
        return QRect(int(ox1), int(oy1), int(ox2 - ox1), int(oy2 - oy1))

    # ------------------------------------------------------------------
    # Hit testing
    # ------------------------------------------------------------------

    def _lane_at_point(self, point: QPoint) -> int:
        """Find the index of the lane at the given overlay position.

        Returns:
            Lane index or -1 if none
        """
        for i, lane in enumerate(self.lanes):
            rect = self._lane_rect_overlay(lane)
            if rect.contains(point):
                return i
        return -1

    def _edge_at_point(self, lane: Lane, point: QPoint) -> Optional[str]:
        """Check if point is near a draggable edge of the lane.

        Returns:
            'left_edge', 'right_edge', or None
        """
        rect = self._lane_rect_overlay(lane)
        margin = HANDLE_SIZE

        # Left edge
        if abs(point.x() - rect.left()) <= margin:
            return 'left_edge'
        # Right edge
        if abs(point.x() - rect.right()) <= margin:
            return 'right_edge'
        return None

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press."""
        pos = event.pos()

        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(pos)
            event.accept()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return

        if self.mode == MODE_DRAW:
            self._drawing = True
            self._draw_start = pos
            self._draw_current = pos
            event.accept()

        elif self.mode == MODE_EDIT:
            lane_idx = self._lane_at_point(pos)
            if lane_idx >= 0:
                lane = self.lanes[lane_idx]
                edge = self._edge_at_point(lane, pos)
                self._selected_lane_idx = lane_idx
                self.lane_selected.emit(lane_idx)

                if edge:
                    self._drag_mode = edge
                else:
                    self._drag_mode = 'move'

                self._drag_start = pos
                self._drag_lane_original = (
                    lane.x_start, lane.x_end, lane.y_start, lane.y_end
                )
            else:
                self._selected_lane_idx = -1
                self._drag_mode = None
            self.update()
            event.accept()

        else:  # VIEW mode
            lane_idx = self._lane_at_point(pos)
            if lane_idx >= 0:
                self._selected_lane_idx = lane_idx
                self.lane_selected.emit(lane_idx)
                self.update()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move."""
        pos = event.pos()

        if self.mode == MODE_DRAW and self._drawing:
            self._draw_current = pos
            self.update()
            event.accept()

        elif self.mode == MODE_EDIT and self._drag_mode and self._drag_start:
            if self._selected_lane_idx < 0 or self._selected_lane_idx >= len(self.lanes):
                event.accept()
                return

            lane = self.lanes[self._selected_lane_idx]
            dx_overlay = pos.x() - self._drag_start.x()
            dx_image = int(dx_overlay * self._scale_x)

            orig_x_start, orig_x_end, orig_y_start, orig_y_end = self._drag_lane_original

            if self._drag_mode == 'move':
                new_x_start = orig_x_start + dx_image
                new_x_end = orig_x_end + dx_image
                lane.x_start = max(0, new_x_start)
                lane.x_end = max(lane.x_start + 1, new_x_end)
                lane.x_position = (lane.x_start + lane.x_end) // 2
                lane.width = lane.x_end - lane.x_start
            elif self._drag_mode == 'left_edge':
                new_x_start = orig_x_start + dx_image
                lane.x_start = max(0, min(new_x_start, lane.x_end - 5))
                lane.x_position = (lane.x_start + lane.x_end) // 2
                lane.width = lane.x_end - lane.x_start
            elif self._drag_mode == 'right_edge':
                new_x_end = orig_x_end + dx_image
                lane.x_end = max(lane.x_start + 5, new_x_end)
                lane.x_position = (lane.x_start + lane.x_end) // 2
                lane.width = lane.x_end - lane.x_start

            self.lane_modified.emit(self._selected_lane_idx, lane)
            self.update()
            event.accept()

        else:
            # Update hover state
            hovered = self._lane_at_point(pos)
            if hovered != self._hovered_lane_idx:
                self._hovered_lane_idx = hovered
                self.update()

            # Update cursor for edge handles
            if self.mode == MODE_EDIT and hovered >= 0:
                edge = self._edge_at_point(self.lanes[hovered], pos)
                if edge:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    self.setCursor(Qt.CursorShape.SizeAllCursor)
            elif self.mode == MODE_DRAW:
                self.setCursor(Qt.CursorShape.CrossCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return

        if self.mode == MODE_DRAW and self._drawing:
            self._drawing = False
            if self._draw_start and self._draw_current:
                self._finalize_draw(self._draw_start, self._draw_current)
            self._draw_start = None
            self._draw_current = None
            self.update()
            event.accept()

        elif self.mode == MODE_EDIT and self._drag_mode:
            self._drag_mode = None
            self._drag_start = None
            self._drag_lane_original = None
            event.accept()

        else:
            # Left-button release in VIEW mode (or DRAW/EDIT when no active
            # operation) – accept to prevent propagation to the parent viewport.
            event.accept()

    def _finalize_draw(self, start: QPoint, end: QPoint) -> None:
        """Create a lane from drawn rectangle."""
        x1_img, y1_img = self._overlay_to_image(start)
        x2_img, y2_img = self._overlay_to_image(end)

        # Normalize coordinates
        x_start = min(x1_img, x2_img)
        x_end = max(x1_img, x2_img)
        y_start = min(y1_img, y2_img)
        y_end = max(y1_img, y2_img)

        if x_end - x_start < 5:
            return

        color = _LANE_COLOR_PALETTE[len(self.lanes) % len(_LANE_COLOR_PALETTE)]

        lane = Lane(
            x_position=(x_start + x_end) // 2,
            width=x_end - x_start,
            height=y_end - y_start if y_end > y_start else 100,
            label=f"Lane {len(self.lanes) + 1}",
            color=color,
            y_start=y_start,
            y_end=y_end if y_end > y_start else y_start + 100,
        )

        self.lanes.append(lane)
        self._selected_lane_idx = len(self.lanes) - 1
        self.lane_added.emit(lane)
        self.update()

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _show_context_menu(self, pos: QPoint) -> None:
        """Show right-click context menu for lane operations."""
        lane_idx = self._lane_at_point(pos)

        menu = QMenu(self)

        if lane_idx >= 0:
            lane = self.lanes[lane_idx]
            menu.addAction(f"Lane: {lane.label or f'Lane {lane_idx + 1}'}")
            menu.addSeparator()
            edit_action = menu.addAction("Edit Properties…")
            delete_action = menu.addAction("Delete Lane")

            action = menu.exec(self.mapToGlobal(pos))

            if action == edit_action:
                self._edit_lane_properties(lane_idx)
            elif action == delete_action:
                self._delete_lane(lane_idx)
        else:
            if self.mode == MODE_DRAW:
                draw_action = menu.addAction("Stop Drawing")
            else:
                draw_action = menu.addAction("Draw New Lane")

            action = menu.exec(self.mapToGlobal(pos))
            if action == draw_action:
                if self.mode == MODE_DRAW:
                    self.set_mode(MODE_VIEW)
                else:
                    self.set_mode(MODE_DRAW)

    def _edit_lane_properties(self, lane_idx: int) -> None:
        """Open a dialog to edit lane properties."""
        if lane_idx < 0 or lane_idx >= len(self.lanes):
            return

        lane = self.lanes[lane_idx]

        dialog = QDialog(self)
        dialog.setWindowTitle("Lane Properties")
        layout = QVBoxLayout()

        # Label
        label_row = QHBoxLayout()
        label_row.addWidget(QLabel("Label:"))
        label_edit = QLineEdit(lane.label)
        label_row.addWidget(label_edit)
        layout.addLayout(label_row)

        # Width
        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Width (px):"))
        width_spin = QSpinBox()
        width_spin.setRange(1, 9999)
        width_spin.setValue(lane.width)
        width_row.addWidget(width_spin)
        layout.addLayout(width_row)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            lane.label = label_edit.text()
            new_width = width_spin.value()
            if new_width != lane.width:
                half = new_width // 2
                lane.x_start = lane.x_position - half
                lane.x_end = lane.x_position + half
                lane.width = new_width
            self.lane_modified.emit(lane_idx, lane)
            self.update()

    def _delete_lane(self, lane_idx: int) -> None:
        """Delete a lane by index."""
        if 0 <= lane_idx < len(self.lanes):
            del self.lanes[lane_idx]
            if self._selected_lane_idx >= len(self.lanes):
                self._selected_lane_idx = len(self.lanes) - 1
            self.lane_removed.emit(lane_idx)
            self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the lane overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw existing lanes
        for i, lane in enumerate(self.lanes):
            self._draw_lane(painter, lane, i)

        # Draw rectangle in progress
        if self._drawing and self._draw_start and self._draw_current:
            self._draw_in_progress(painter, self._draw_start, self._draw_current)

        painter.end()

    def _draw_lane(self, painter: QPainter, lane: Lane, idx: int) -> None:
        """Draw a single lane rectangle."""
        rect = self._lane_rect_overlay(lane)
        color = QColor(*lane.color)

        is_selected = idx == self._selected_lane_idx
        is_hovered = idx == self._hovered_lane_idx

        # Fill
        fill_color = QColor(color)
        fill_color.setAlpha(60 if is_selected else (40 if is_hovered else 25))
        painter.fillRect(rect, QBrush(fill_color))

        # Border
        pen_width = 2 if is_selected else 1
        border_color = QColor(color)
        border_color.setAlpha(220 if is_selected else (180 if is_hovered else 140))
        painter.setPen(QPen(border_color, pen_width))
        painter.drawRect(rect)

        # Draw edge handles when selected or in edit mode
        if is_selected or (self.mode == MODE_EDIT and is_hovered):
            handle_color = QColor(color)
            handle_color.setAlpha(200)
            painter.setBrush(QBrush(handle_color))
            painter.setPen(QPen(QColor("white"), 1))
            h = HANDLE_SIZE

            # Left edge handle
            left_handle = QRect(rect.left() - h // 2, rect.center().y() - h // 2, h, h)
            painter.drawRect(left_handle)

            # Right edge handle
            right_handle = QRect(rect.right() - h // 2, rect.center().y() - h // 2, h, h)
            painter.drawRect(right_handle)

        # Draw label
        label = lane.label or f"Lane {idx + 1}"
        text_color = QColor(color)
        text_color.setAlpha(230)
        painter.setPen(QPen(text_color))
        font = painter.font()
        font.setPointSize(8)
        font.setBold(is_selected)
        painter.setFont(font)
        painter.drawText(rect.left() + 3, rect.top() + 12, label)

    def _draw_in_progress(self, painter: QPainter, start: QPoint, end: QPoint) -> None:
        """Draw the rectangle currently being drawn."""
        x = min(start.x(), end.x())
        y = min(start.y(), end.y())
        w = abs(end.x() - start.x())
        h = abs(end.y() - start.y())
        rect = QRect(x, y, w, h)

        fill = QColor(100, 160, 255, 40)
        painter.fillRect(rect, fill)
        painter.setPen(QPen(QColor(100, 160, 255, 200), 1, Qt.PenStyle.DashLine))
        painter.drawRect(rect)
