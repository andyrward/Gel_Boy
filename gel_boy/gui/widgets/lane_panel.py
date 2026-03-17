"""Lane management panel widget."""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QListWidget, QListWidgetItem, QLabel,
    QSpinBox, QLineEdit, QColorDialog,
    QButtonGroup, QRadioButton
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor, QBrush
from gel_boy.models.lane import Lane


class LanePanel(QWidget):
    """Side panel widget for managing gel lanes.

    Provides controls for:
    - Automatic lane detection
    - Manual lane drawing toggle
    - Lane list with selection
    - Lane property editing (label, color, width)
    - Profile calculation options (mean/median)

    Signals:
        detect_lanes_clicked(): User requested auto detection
        draw_lane_toggled(bool): Drawing mode enabled/disabled
        lane_selected(int): User selected lane by index
        lane_deleted(int): User deleted lane by index
        calculate_profiles_clicked(str): User requested profile calculation ('mean'/'median')
        clear_lanes_clicked(): User requested to clear all lanes
        update_plot_clicked(): User requested to update the plot
    """

    detect_lanes_clicked = pyqtSignal()
    draw_lane_toggled = pyqtSignal(bool)
    edit_lane_toggled = pyqtSignal(bool)
    lane_selected = pyqtSignal(int)
    lane_deleted = pyqtSignal(int)
    lane_width_changed = pyqtSignal(int, object)   # (index, Lane)
    calculate_profiles_clicked = pyqtSignal(str)   # 'mean' or 'median'
    clear_lanes_clicked = pyqtSignal()
    update_plot_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the lane panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setMinimumWidth(220)
        self._lanes: List[Lane] = []
        self._drawing_mode: bool = False
        self._editing_mode: bool = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the panel layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # ------ Detection Controls ------
        detect_group = QGroupBox("Lane Detection")
        detect_layout = QVBoxLayout()
        detect_layout.setContentsMargins(4, 6, 4, 4)
        detect_layout.setSpacing(4)

        # Min/max lane width
        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Min W:"))
        self.min_width_spin = QSpinBox()
        self.min_width_spin.setRange(1, 500)
        self.min_width_spin.setValue(20)
        self.min_width_spin.setToolTip("Minimum lane width in pixels")
        width_row.addWidget(self.min_width_spin)
        width_row.addWidget(QLabel("Max W:"))
        self.max_width_spin = QSpinBox()
        self.max_width_spin.setRange(1, 2000)
        self.max_width_spin.setValue(100)
        self.max_width_spin.setToolTip("Maximum lane width in pixels")
        width_row.addWidget(self.max_width_spin)
        detect_layout.addLayout(width_row)

        self.detect_btn = QPushButton("Auto Detect Lanes")
        self.detect_btn.setToolTip("Automatically detect lanes using intensity projection (Ctrl+L)")
        self.detect_btn.setEnabled(False)
        self.detect_btn.clicked.connect(self.detect_lanes_clicked.emit)
        detect_layout.addWidget(self.detect_btn)

        detect_group.setLayout(detect_layout)
        layout.addWidget(detect_group)

        # ------ Manual Drawing ------
        draw_group = QGroupBox("Manual Drawing")
        draw_layout = QVBoxLayout()
        draw_layout.setContentsMargins(4, 6, 4, 4)
        draw_layout.setSpacing(4)

        self.draw_btn = QPushButton("Draw Lane")
        self.draw_btn.setCheckable(True)
        self.draw_btn.setToolTip("Toggle lane drawing mode (Ctrl+Shift+L)")
        self.draw_btn.setEnabled(False)
        self.draw_btn.toggled.connect(self._on_draw_toggled)
        draw_layout.addWidget(self.draw_btn)

        self.edit_btn = QPushButton("Edit Lanes")
        self.edit_btn.setCheckable(True)
        self.edit_btn.setToolTip("Toggle lane editing mode — drag lanes to move/resize")
        self.edit_btn.setEnabled(False)
        self.edit_btn.toggled.connect(self._on_edit_toggled)
        draw_layout.addWidget(self.edit_btn)

        draw_group.setLayout(draw_layout)
        layout.addWidget(draw_group)

        # ------ Lane List ------
        list_group = QGroupBox("Lanes")
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(4, 6, 4, 4)
        list_layout.setSpacing(4)

        self.lanes_list = QListWidget()
        self.lanes_list.setMaximumHeight(160)
        self.lanes_list.setToolTip("Click to select a lane")
        self.lanes_list.currentRowChanged.connect(self._on_lane_selected)
        list_layout.addWidget(self.lanes_list)

        list_btn_row = QHBoxLayout()
        self.delete_lane_btn = QPushButton("Delete")
        self.delete_lane_btn.setEnabled(False)
        self.delete_lane_btn.clicked.connect(self._on_delete_lane)
        list_btn_row.addWidget(self.delete_lane_btn)

        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.setEnabled(False)
        self.clear_all_btn.clicked.connect(self.clear_lanes_clicked.emit)
        list_btn_row.addWidget(self.clear_all_btn)
        list_layout.addLayout(list_btn_row)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # ------ Lane Properties ------
        props_group = QGroupBox("Lane Properties")
        props_layout = QVBoxLayout()
        props_layout.setContentsMargins(4, 6, 4, 4)
        props_layout.setSpacing(4)

        label_row = QHBoxLayout()
        label_row.addWidget(QLabel("Label:"))
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Lane name…")
        self.label_edit.setEnabled(False)
        self.label_edit.editingFinished.connect(self._on_label_changed)
        label_row.addWidget(self.label_edit)
        props_layout.addLayout(label_row)

        width_adj_row = QHBoxLayout()
        width_adj_row.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 2000)
        self.width_spin.setEnabled(False)
        self.width_spin.valueChanged.connect(self._on_width_changed)
        width_adj_row.addWidget(self.width_spin)
        width_adj_row.addWidget(QLabel("px"))
        props_layout.addLayout(width_adj_row)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color:"))
        self.color_btn = QPushButton("  ")
        self.color_btn.setEnabled(False)
        self.color_btn.setFixedWidth(40)
        self.color_btn.clicked.connect(self._on_pick_color)
        color_row.addWidget(self.color_btn)
        color_row.addStretch()
        props_layout.addLayout(color_row)

        props_group.setLayout(props_layout)
        layout.addWidget(props_group)

        # ------ Profile Options ------
        profile_group = QGroupBox("Intensity Profiles")
        profile_layout = QVBoxLayout()
        profile_layout.setContentsMargins(4, 6, 4, 4)
        profile_layout.setSpacing(4)

        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self._profile_type_group = QButtonGroup(self)
        self.mean_radio = QRadioButton("Mean")
        self.mean_radio.setChecked(True)
        self.median_radio = QRadioButton("Median")
        self._profile_type_group.addButton(self.mean_radio)
        self._profile_type_group.addButton(self.median_radio)
        type_row.addWidget(self.mean_radio)
        type_row.addWidget(self.median_radio)
        profile_layout.addLayout(type_row)

        self.calc_profiles_btn = QPushButton("Calculate Profiles")
        self.calc_profiles_btn.setEnabled(False)
        self.calc_profiles_btn.clicked.connect(self._on_calculate_profiles)
        profile_layout.addWidget(self.calc_profiles_btn)

        self.update_plot_btn = QPushButton("Update Plot")
        self.update_plot_btn.setEnabled(False)
        self.update_plot_btn.clicked.connect(self.update_plot_clicked.emit)
        profile_layout.addWidget(self.update_plot_btn)

        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)

        layout.addStretch()
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_image_loaded(self, loaded: bool) -> None:
        """Enable or disable controls based on whether an image is loaded.

        Args:
            loaded: True if an image is loaded
        """
        self.detect_btn.setEnabled(loaded)
        self.draw_btn.setEnabled(loaded)
        self.edit_btn.setEnabled(loaded)

    def set_lanes(self, lanes: List[Lane]) -> None:
        """Update the lanes list widget.

        Args:
            lanes: Current list of Lane objects
        """
        self._lanes = lanes
        self.lanes_list.blockSignals(True)
        self.lanes_list.clear()

        for i, lane in enumerate(lanes):
            label = lane.label or f"Lane {i + 1}"
            item = QListWidgetItem(label)
            color = QColor(*lane.color)
            item.setBackground(QBrush(QColor(color.red(), color.green(), color.blue(), 80)))
            self.lanes_list.addItem(item)

        self.lanes_list.blockSignals(False)

        has_lanes = len(lanes) > 0
        self.clear_all_btn.setEnabled(has_lanes)
        self.calc_profiles_btn.setEnabled(has_lanes)
        self.update_plot_btn.setEnabled(has_lanes)

    def set_selected_lane(self, index: int) -> None:
        """Update the selected lane in the list and properties panel.

        Args:
            index: Lane index to select (-1 to deselect)
        """
        self.lanes_list.blockSignals(True)
        self.lanes_list.setCurrentRow(index)
        self.lanes_list.blockSignals(False)

        if 0 <= index < len(self._lanes):
            lane = self._lanes[index]
            self.label_edit.setEnabled(True)
            self.label_edit.blockSignals(True)
            self.label_edit.setText(lane.label)
            self.label_edit.blockSignals(False)

            self.width_spin.setEnabled(True)
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(lane.width)
            self.width_spin.blockSignals(False)

            self.color_btn.setEnabled(True)
            color = QColor(*lane.color)
            self.color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid gray;"
            )
            self.delete_lane_btn.setEnabled(True)
        else:
            self.label_edit.setEnabled(False)
            self.width_spin.setEnabled(False)
            self.color_btn.setEnabled(False)
            self.delete_lane_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_draw_toggled(self, checked: bool) -> None:
        """Handle draw button toggle — disables edit mode when activated."""
        self._drawing_mode = checked
        self.draw_btn.setText("Stop Drawing" if checked else "Draw Lane")
        if checked and self._editing_mode:
            # Turn off edit mode
            self.edit_btn.blockSignals(True)
            self.edit_btn.setChecked(False)
            self.edit_btn.setText("Edit Lanes")
            self.edit_btn.blockSignals(False)
            self._editing_mode = False
            self.edit_lane_toggled.emit(False)
        self.draw_lane_toggled.emit(checked)

    def _on_edit_toggled(self, checked: bool) -> None:
        """Handle edit button toggle — disables draw mode when activated."""
        self._editing_mode = checked
        self.edit_btn.setText("Stop Editing" if checked else "Edit Lanes")
        if checked and self._drawing_mode:
            # Turn off draw mode
            self.draw_btn.blockSignals(True)
            self.draw_btn.setChecked(False)
            self.draw_btn.setText("Draw Lane")
            self.draw_btn.blockSignals(False)
            self._drawing_mode = False
            self.draw_lane_toggled.emit(False)
        self.edit_lane_toggled.emit(checked)

    def _on_lane_selected(self, row: int) -> None:
        """Handle lane list selection change."""
        if row >= 0:
            self.lane_selected.emit(row)
            self.set_selected_lane(row)

    def _on_delete_lane(self) -> None:
        """Handle delete lane button."""
        row = self.lanes_list.currentRow()
        if row >= 0:
            self.lane_deleted.emit(row)

    def _on_label_changed(self) -> None:
        """Handle lane label edit."""
        row = self.lanes_list.currentRow()
        if 0 <= row < len(self._lanes):
            self._lanes[row].label = self.label_edit.text()
            self.lanes_list.item(row).setText(self.label_edit.text() or f"Lane {row + 1}")

    def _on_width_changed(self, value: int) -> None:
        """Handle width spinbox change — clamps boundaries and emits lane_width_changed."""
        row = self.lanes_list.currentRow()
        if 0 <= row < len(self._lanes):
            lane = self._lanes[row]
            half = value // 2
            x_start = max(0, lane.x_position - half)
            lane.x_start = x_start
            lane.x_end = x_start + value
            lane.width = value
            self.lane_width_changed.emit(row, lane)

    def _on_pick_color(self) -> None:
        """Open color picker dialog."""
        row = self.lanes_list.currentRow()
        if 0 <= row < len(self._lanes):
            lane = self._lanes[row]
            initial = QColor(*lane.color)
            color = QColorDialog.getColor(initial, self, "Choose Lane Color")
            if color.isValid():
                lane.color = (color.red(), color.green(), color.blue())
                self.color_btn.setStyleSheet(
                    f"background-color: {color.name()}; border: 1px solid gray;"
                )
                # Update list item color
                item = self.lanes_list.item(row)
                if item:
                    item.setBackground(QBrush(
                        QColor(color.red(), color.green(), color.blue(), 80)
                    ))

    def _on_calculate_profiles(self) -> None:
        """Emit calculate_profiles_clicked with current profile type."""
        profile_type = 'mean' if self.mean_radio.isChecked() else 'median'
        self.calculate_profiles_clicked.emit(profile_type)

    def get_min_lane_width(self) -> int:
        """Return minimum lane width setting."""
        return self.min_width_spin.value()

    def get_max_lane_width(self) -> int:
        """Return maximum lane width setting."""
        return self.max_width_spin.value()
