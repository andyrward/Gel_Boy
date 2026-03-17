"""Interactive intensity profile plot widget for gel analysis."""

from typing import Optional, List, Tuple, Dict
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QSlider, QComboBox, QTableWidget,
    QTableWidgetItem, QGroupBox, QSizePolicy, QFileDialog,
    QSplitter, QToolBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
import matplotlib.patches as mpatches


# Interaction modes
PLOT_MODE_VIEW = "view"
PLOT_MODE_INTEGRATE = "integrate"
PLOT_MODE_BACKGROUND = "background"

# Default colors for multiple lanes
LANE_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]


class IntensityPlotWidget(QWidget):
    """Interactive matplotlib widget for intensity profile visualization.

    Features:
    - Plot mean/median intensity profiles for one or more lanes
    - Peak integration by click-drag selection
    - Background correction by clicking reference points
    - Zoom/pan via NavigationToolbar2QT
    - Smoothing slider
    - Export to PNG/SVG
    - Table of integration results

    Signals:
        peak_integrated(int, int, float): lane_id, start_idx, end_idx, area
        background_updated(int, list): lane_id, background_points
    """

    peak_integrated = pyqtSignal(int, int, int, float)  # lane_id, start, end, area
    background_updated = pyqtSignal(int, list)           # lane_id, points

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(200)

        # Data storage
        self._profiles: Dict[int, Dict] = {}   # lane_id -> {mean, median, label, color}
        self._active_lane_ids: List[int] = []
        self._smoothing: int = 1

        # Profile type
        self._profile_type: str = 'mean'

        # Plot mode
        self._mode: str = PLOT_MODE_VIEW

        # Peak integration state
        self._integration_regions: Dict[int, List[Dict]] = {}  # lane_id -> list of regions
        self._span_start: Optional[float] = None
        self._span_rect = None

        # Background points state
        self._background_points: Dict[int, List[Tuple[int, float]]] = {}  # lane_id -> [(x, y)]
        self._bg_markers: List = []
        self._bg_line_artists: List = []

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the widget layout."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)

        # Controls toolbar (top)
        controls = self._build_controls()
        main_layout.addLayout(controls)

        # Splitter: plot on top, table on bottom
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Plot area
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        plot_layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(8, 3), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.ax = self.figure.add_subplot(111)
        self._setup_axes()

        self.nav_toolbar = NavigationToolbar2QT(self.canvas, plot_widget)
        plot_layout.addWidget(self.nav_toolbar)
        plot_layout.addWidget(self.canvas)
        plot_widget.setLayout(plot_layout)
        splitter.addWidget(plot_widget)

        # Results table
        table_group = QGroupBox("Integration Results")
        table_layout = QVBoxLayout()
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(
            ["Lane", "Start", "End", "Raw Area", "Corrected Area"]
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setMaximumHeight(120)
        table_layout.addWidget(self.results_table)
        table_group.setLayout(table_layout)
        splitter.addWidget(table_group)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

        # Connect canvas events
        self.canvas.mpl_connect('button_press_event', self._on_plot_press)
        self.canvas.mpl_connect('motion_notify_event', self._on_plot_motion)
        self.canvas.mpl_connect('button_release_event', self._on_plot_release)

    def _build_controls(self) -> QHBoxLayout:
        """Build the controls row above the plot."""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Mode selector
        mode_group = QGroupBox("Mode")
        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(4, 2, 4, 2)

        self._mode_buttons = QButtonGroup(self)
        for label, mode in [
            ("View", PLOT_MODE_VIEW),
            ("Integrate", PLOT_MODE_INTEGRATE),
            ("Background", PLOT_MODE_BACKGROUND),
        ]:
            btn = QRadioButton(label)
            btn.setProperty("mode", mode)
            if mode == PLOT_MODE_VIEW:
                btn.setChecked(True)
            self._mode_buttons.addButton(btn)
            mode_layout.addWidget(btn)

        self._mode_buttons.buttonClicked.connect(self._on_mode_changed)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Profile type
        type_group = QGroupBox("Profile")
        type_layout = QHBoxLayout()
        type_layout.setContentsMargins(4, 2, 4, 2)
        self._type_buttons = QButtonGroup(self)

        self._mean_radio = QRadioButton("Mean")
        self._mean_radio.setChecked(True)
        self._median_radio = QRadioButton("Median")
        self._type_buttons.addButton(self._mean_radio)
        self._type_buttons.addButton(self._median_radio)
        self._type_buttons.buttonClicked.connect(self._on_profile_type_changed)
        type_layout.addWidget(self._mean_radio)
        type_layout.addWidget(self._median_radio)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Smoothing
        smooth_group = QGroupBox("Smoothing")
        smooth_layout = QHBoxLayout()
        smooth_layout.setContentsMargins(4, 2, 4, 2)
        self._smooth_label = QLabel("1")
        self._smooth_slider = QSlider(Qt.Orientation.Horizontal)
        self._smooth_slider.setRange(1, 51)
        self._smooth_slider.setSingleStep(2)
        self._smooth_slider.setValue(1)
        self._smooth_slider.setMaximumWidth(100)
        self._smooth_slider.valueChanged.connect(self._on_smoothing_changed)
        smooth_layout.addWidget(self._smooth_slider)
        smooth_layout.addWidget(self._smooth_label)
        smooth_group.setLayout(smooth_layout)
        layout.addWidget(smooth_group)

        # Action buttons
        self._clear_bg_btn = QPushButton("Clear BG Points")
        self._clear_bg_btn.setToolTip("Clear all background reference points")
        self._clear_bg_btn.clicked.connect(self._clear_background_points)
        layout.addWidget(self._clear_bg_btn)

        self._clear_int_btn = QPushButton("Clear Integrations")
        self._clear_int_btn.setToolTip("Clear all integration regions")
        self._clear_int_btn.clicked.connect(self._clear_integrations)
        layout.addWidget(self._clear_int_btn)

        export_btn = QPushButton("Export Plot")
        export_btn.setToolTip("Export the current plot as PNG or SVG")
        export_btn.clicked.connect(self._export_plot)
        layout.addWidget(export_btn)

        layout.addStretch()
        return layout

    def _setup_axes(self) -> None:
        """Configure axes appearance."""
        self.ax.set_xlabel("Position (pixels)")
        self.ax.set_ylabel("Intensity")
        self.ax.set_title("Intensity Profile")
        self.ax.grid(True, alpha=0.3)
        self.figure.tight_layout(pad=1.5)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_profile(
        self,
        lane_id: int,
        mean_profile: Optional[np.ndarray],
        median_profile: Optional[np.ndarray],
        label: str = "",
        color: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        """Add or update the profile data for a lane.

        Args:
            lane_id: Unique ID for the lane
            mean_profile: 1D array of mean intensity values
            median_profile: 1D array of median intensity values
            label: Display name for the lane
            color: RGB tuple for the lane color, or None for auto
        """
        color_str = (
            '#{:02x}{:02x}{:02x}'.format(*color)
            if color else LANE_COLORS[lane_id % len(LANE_COLORS)]
        )
        self._profiles[lane_id] = {
            'mean': mean_profile,
            'median': median_profile,
            'label': label or f"Lane {lane_id + 1}",
            'color': color_str,
        }
        if lane_id not in self._active_lane_ids:
            self._active_lane_ids.append(lane_id)
        self._update_plot()

    def remove_lane(self, lane_id: int) -> None:
        """Remove a lane from the plot.

        Args:
            lane_id: Lane ID to remove
        """
        self._profiles.pop(lane_id, None)
        if lane_id in self._active_lane_ids:
            self._active_lane_ids.remove(lane_id)
        self._integration_regions.pop(lane_id, None)
        self._background_points.pop(lane_id, None)
        self._update_plot()

    def clear_all(self) -> None:
        """Clear all profiles and results."""
        self._profiles.clear()
        self._active_lane_ids.clear()
        self._integration_regions.clear()
        self._background_points.clear()
        self._update_plot()

    def set_active_lanes(self, lane_ids: List[int]) -> None:
        """Set which lanes are shown in the plot.

        Args:
            lane_ids: List of lane IDs to display
        """
        self._active_lane_ids = [lid for lid in lane_ids if lid in self._profiles]
        self._update_plot()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_mode_changed(self, btn) -> None:
        """Handle mode radio button change."""
        mode = btn.property("mode")
        if mode:
            self._mode = mode
            # Disable navigation toolbar in interactive modes
            nav_enabled = (mode == PLOT_MODE_VIEW)
            for action in self.nav_toolbar.actions():
                action.setEnabled(nav_enabled)

    def _on_profile_type_changed(self, btn) -> None:
        """Handle profile type change."""
        self._profile_type = 'mean' if btn == self._mean_radio else 'median'
        self._update_plot()

    def _on_smoothing_changed(self, value: int) -> None:
        """Handle smoothing slider change."""
        # Snap to odd values for moving average symmetry
        if value % 2 == 0:
            value = value + 1
        self._smoothing = value
        self._smooth_label.setText(str(value))
        self._update_plot()

    def _clear_background_points(self) -> None:
        """Clear all background reference points."""
        for lane_id in list(self._background_points.keys()):
            self._background_points[lane_id] = []
            self.background_updated.emit(lane_id, [])
        self._update_plot()

    def _clear_integrations(self) -> None:
        """Clear all integration regions."""
        self._integration_regions.clear()
        self.results_table.setRowCount(0)
        self._update_plot()

    def _export_plot(self) -> None:
        """Export the current plot to file."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            "intensity_profile.png",
            "PNG Image (*.png);;SVG Image (*.svg);;All Files (*)"
        )
        if path:
            self.figure.savefig(path, dpi=150, bbox_inches='tight')

    # ------------------------------------------------------------------
    # Mouse interaction on plot
    # ------------------------------------------------------------------

    def _on_plot_press(self, event) -> None:
        """Handle matplotlib canvas click."""
        if event.inaxes != self.ax or event.xdata is None:
            return

        if self._mode == PLOT_MODE_INTEGRATE:
            self._span_start = event.xdata
            # Remove any existing span rectangle
            if self._span_rect is not None:
                try:
                    self._span_rect.remove()
                except Exception:
                    pass
            self._span_rect = None

        elif self._mode == PLOT_MODE_BACKGROUND:
            # Add background point at click position for the first active lane
            if not self._active_lane_ids:
                return
            lane_id = self._active_lane_ids[0]
            x = int(round(event.xdata))
            y = float(event.ydata)
            if lane_id not in self._background_points:
                self._background_points[lane_id] = []
            self._background_points[lane_id].append((x, y))
            self.background_updated.emit(lane_id, self._background_points[lane_id])
            self._update_plot()

    def _on_plot_motion(self, event) -> None:
        """Handle matplotlib canvas mouse move."""
        if (self._mode == PLOT_MODE_INTEGRATE and
                self._span_start is not None and
                event.inaxes == self.ax and
                event.xdata is not None):

            # Update span rectangle
            x0 = min(self._span_start, event.xdata)
            x1 = max(self._span_start, event.xdata)

            if self._span_rect is not None:
                try:
                    self._span_rect.remove()
                except Exception:
                    pass

            self._span_rect = self.ax.axvspan(x0, x1, alpha=0.25, color='yellow', zorder=5)
            self.canvas.draw_idle()

    def _on_plot_release(self, event) -> None:
        """Handle matplotlib canvas mouse release."""
        if (self._mode == PLOT_MODE_INTEGRATE and
                self._span_start is not None and
                event.inaxes == self.ax and
                event.xdata is not None):

            x0 = min(self._span_start, event.xdata)
            x1 = max(self._span_start, event.xdata)
            self._span_start = None

            if abs(x1 - x0) < 2:
                return

            start_idx = max(0, int(round(x0)))
            end_idx = int(round(x1))

            # Integrate for all active lanes
            for lane_id in self._active_lane_ids:
                self._integrate_region(lane_id, start_idx, end_idx)

            self._update_plot()

    # ------------------------------------------------------------------
    # Integration logic
    # ------------------------------------------------------------------

    def _get_display_profile(self, lane_id: int) -> Optional[np.ndarray]:
        """Get the (smoothed) profile to display for a lane."""
        info = self._profiles.get(lane_id)
        if info is None:
            return None

        raw = info.get(self._profile_type)
        if raw is None:
            raw = info.get('mean')
        if raw is None or len(raw) == 0:
            return None

        if self._smoothing > 1:
            from gel_boy.core.intensity_analysis import smooth_profile
            return smooth_profile(raw, self._smoothing)
        return raw

    def _integrate_region(self, lane_id: int, start_idx: int, end_idx: int) -> None:
        """Integrate a peak region for a lane."""
        profile = self._get_display_profile(lane_id)
        if profile is None:
            return

        from gel_boy.core.intensity_analysis import integrate_peak
        bg_points = self._background_points.get(lane_id)
        result = integrate_peak(profile, start_idx, end_idx, bg_points)

        region = {
            'start': start_idx,
            'end': end_idx,
            'raw_area': result['raw_area'],
            'corrected_area': result['corrected_area'],
        }

        if lane_id not in self._integration_regions:
            self._integration_regions[lane_id] = []
        self._integration_regions[lane_id].append(region)

        self.peak_integrated.emit(lane_id, start_idx, end_idx, result['corrected_area'])
        self._update_results_table()

    def _update_results_table(self) -> None:
        """Refresh the integration results table."""
        rows = []
        for lane_id, regions in self._integration_regions.items():
            info = self._profiles.get(lane_id, {})
            label = info.get('label', f"Lane {lane_id + 1}")
            for r in regions:
                corrected = r.get('corrected_area')
                corrected_str = f"{corrected:.1f}" if corrected is not None else "—"
                rows.append((label, str(r['start']), str(r['end']),
                              f"{r['raw_area']:.1f}", corrected_str))

        self.results_table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            for col_idx, val in enumerate(row_data):
                self.results_table.setItem(row_idx, col_idx, QTableWidgetItem(val))

    # ------------------------------------------------------------------
    # Plot rendering
    # ------------------------------------------------------------------

    def _update_plot(self) -> None:
        """Redraw the intensity profile plot."""
        self.ax.clear()
        self._setup_axes()

        if not self._active_lane_ids:
            self.canvas.draw_idle()
            return

        for lane_id in self._active_lane_ids:
            info = self._profiles.get(lane_id)
            if info is None:
                continue

            profile = self._get_display_profile(lane_id)
            if profile is None or len(profile) == 0:
                continue

            color = info['color']
            label = info['label']
            x = np.arange(len(profile))
            self.ax.plot(x, profile, color=color, label=label, linewidth=1.5)

            # Draw background line if we have bg points
            bg_points = self._background_points.get(lane_id, [])
            if len(bg_points) >= 2:
                from gel_boy.core.intensity_analysis import subtract_linear_background
                bg_line, _, slope, intercept = subtract_linear_background(profile, bg_points)
                self.ax.plot(x, bg_line, '--', color=color, alpha=0.5,
                             label=f"{label} BG", linewidth=1)

            # Draw background point markers
            if bg_points:
                bx = [p[0] for p in bg_points]
                by = [p[1] for p in bg_points]
                self.ax.scatter(bx, by, color=color, marker='x', s=60, zorder=10,
                                label=f"{label} BG pts")

            # Draw integration regions
            regions = self._integration_regions.get(lane_id, [])
            for reg in regions:
                self.ax.axvspan(reg['start'], reg['end'], alpha=0.2, color=color)
                # Annotate with area
                mid = (reg['start'] + reg['end']) / 2
                y_top = float(np.max(
                    profile[max(0, reg['start']):min(len(profile), reg['end'])]
                ))
                area = reg.get('corrected_area') or reg['raw_area']
                self.ax.annotate(
                    f"{area:.0f}",
                    xy=(mid, y_top),
                    xytext=(0, 6),
                    textcoords='offset points',
                    ha='center', fontsize=7, color=color,
                )

        if len(self._active_lane_ids) > 1 or any(
            self._background_points.get(lid) for lid in self._active_lane_ids
        ):
            self.ax.legend(fontsize=8, loc='upper right')

        self.canvas.draw_idle()
