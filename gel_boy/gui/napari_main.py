"""Main napari-based application class for Gel_Boy.

Replaces the PyQt6 ``MainWindow`` / ``ImageViewer`` pair with a napari
viewer, eliminating the coordinate-transformation bugs that existed in the
previous custom QGraphicsView implementation.  All gel-specific analysis
algorithms remain in their original modules and are called unchanged.

Usage::

    from gel_boy.gui.napari_main import GelBoyNapariApp

    app = GelBoyNapariApp()
    app.run()
"""

from __future__ import annotations

import sys
from typing import List, Optional

import numpy as np


class GelBoyNapariApp:
    """Gel_Boy application built on a napari viewer.

    Attributes:
        viewer: The underlying ``napari.Viewer`` instance.
        lanes:  List of :class:`~gel_boy.models.lane.Lane` objects currently
                defined in the session.
    """

    # Names used for napari layers so they can be retrieved by name.
    _IMAGE_LAYER = "Gel Image"
    _LANES_LAYER = "Lanes"

    def __init__(self) -> None:
        import napari

        self.viewer: napari.Viewer = napari.Viewer(title="Gel_Boy")
        self.lanes: List = []
        self._original_pil_image = None   # PIL Image for reset (never mutated)
        self._current_pil_image = None    # PIL Image reflecting applied operations
        self._profiles: List[np.ndarray] = []
        self._updating_lanes: bool = False  # guard against callback re-entry

        self._setup_widgets()
        self._setup_keybindings()
        self._ensure_lanes_layer()
        self._setup_lanes_callbacks()

    # ------------------------------------------------------------------
    # Widget / keybinding setup
    # ------------------------------------------------------------------

    def _setup_widgets(self) -> None:
        """Add all dock widgets to the napari viewer."""
        from gel_boy.gui.napari_widgets import (
            make_lane_detection_widget,
            make_profile_widget,
            make_peak_integration_widget,
            make_image_ops_widget,
            make_file_ops_widget,
            make_rotation_widget,
        )

        self.viewer.window.add_dock_widget(
            make_file_ops_widget(self),
            name="File",
            area="left",
        )
        self.viewer.window.add_dock_widget(
            make_image_ops_widget(self),
            name="Image Operations",
            area="left",
        )
        self.viewer.window.add_dock_widget(
            make_rotation_widget(self),
            name="Rotation",
            area="left",
        )
        self.viewer.window.add_dock_widget(
            make_lane_detection_widget(self),
            name="Lane Detection",
            area="right",
        )
        self.viewer.window.add_dock_widget(
            make_profile_widget(self),
            name="Intensity Profiles",
            area="right",
        )
        self.viewer.window.add_dock_widget(
            make_peak_integration_widget(self),
            name="Peak Integration",
            area="right",
        )

    def _setup_keybindings(self) -> None:
        """Register keyboard shortcuts on the napari viewer."""

        @self.viewer.bind_key("ctrl+l")
        def _kb_detect_lanes(viewer):
            self.detect_lanes()

        @self.viewer.bind_key("ctrl+p")
        def _kb_calculate_profiles(viewer):
            self.calculate_profiles()

        @self.viewer.bind_key("d")
        def _kb_draw_lane(viewer):
            """Toggle rectangle-drawing mode on the Lanes layer."""
            self._toggle_lane_drawing()

    # ------------------------------------------------------------------
    # Lane layer helpers
    # ------------------------------------------------------------------

    def _ensure_lanes_layer(self) -> None:
        """Create the Lanes Shapes layer if it does not yet exist."""
        if self._LANES_LAYER not in self.viewer.layers:
            self.viewer.add_shapes(
                [],
                shape_type="rectangle",
                edge_color="cyan",
                face_color=[0, 1, 1, 0.3],
                edge_width=2,
                name=self._LANES_LAYER,
            )

    def _setup_lanes_callbacks(self) -> None:
        """Connect the Lanes layer data-changed event to the sync callback."""
        if self._LANES_LAYER in self.viewer.layers:
            layer = self.viewer.layers[self._LANES_LAYER]
            layer.events.data.connect(self._on_lanes_layer_changed)

    def _on_lanes_layer_changed(self, event=None) -> None:
        """Sync ``self.lanes`` when the user manually adds/edits shapes."""
        if self._updating_lanes:
            return
        self._sync_lanes_from_layer()

    def _toggle_lane_drawing(self) -> None:
        """Toggle rectangle-drawing mode on the Lanes layer."""
        if self._LANES_LAYER in self.viewer.layers:
            layer = self.viewer.layers[self._LANES_LAYER]
            if layer.mode == "add_rectangle":
                layer.mode = "pan_zoom"
            else:
                layer.mode = "add_rectangle"

    # ------------------------------------------------------------------
    # Image loading
    # ------------------------------------------------------------------

    def load_image(self, filepath: str) -> bool:
        """Load a gel image into the napari viewer.

        Args:
            filepath: Path to the image file (TIFF, PNG, JPEG, BMP, GIF).

        Returns:
            ``True`` on success, ``False`` if the file could not be loaded.
        """
        from gel_boy.io.image_loader import load_image
        from gel_boy.gui.napari_utils import pil_image_to_numpy

        pil_image = load_image(filepath)
        if pil_image is None:
            return False

        self._original_pil_image = pil_image
        self._current_pil_image = pil_image
        arr = pil_image_to_numpy(pil_image)
        self._set_image_data(arr)
        return True

    def _set_image_data(self, arr: np.ndarray) -> None:
        """Replace or create the Gel Image layer with *arr*."""
        if self._IMAGE_LAYER in self.viewer.layers:
            self.viewer.layers[self._IMAGE_LAYER].data = arr
        else:
            colormap = "gray"
            self.viewer.add_image(arr, name=self._IMAGE_LAYER, colormap=colormap)

    # ------------------------------------------------------------------
    # Lane management
    # ------------------------------------------------------------------

    def _get_image_array(self) -> Optional[np.ndarray]:
        """Return the current image data or None if no image is loaded."""
        if self._IMAGE_LAYER not in self.viewer.layers:
            return None
        return np.asarray(self.viewer.layers[self._IMAGE_LAYER].data)

    def detect_lanes(
        self,
        min_lane_width: int = 20,
        max_lane_width: int = 100,
    ) -> None:
        """Run auto-detection and add results to the viewer.

        Uses :func:`gel_boy.core.lane_detection.detect_lanes` unchanged.

        Args:
            min_lane_width: Minimum lane width passed to the detector.
            max_lane_width: Maximum lane width passed to the detector.
        """
        from gel_boy.core.lane_detection import detect_lanes
        from gel_boy.models.lane import Lane

        arr = self._get_image_array()
        if arr is None:
            return

        img_height = arr.shape[0]
        detections = detect_lanes(
            arr,
            min_lane_width=min_lane_width,
            max_lane_width=max_lane_width,
        )

        self.lanes = [
            Lane(
                x_position=x_pos,
                width=width,
                height=img_height,
                label=f"Lane {i + 1}",
                y_start=0,
                y_end=img_height,
            )
            for i, (x_pos, width) in enumerate(detections)
        ]
        self._update_lanes_layer()

    def _update_lanes_layer(self) -> None:
        """Synchronise the Lanes Shapes layer with ``self.lanes``."""
        from gel_boy.gui.napari_utils import (
            lanes_to_napari_rects,
            lane_colors_for_napari,
            build_lane_properties,
        )

        self._ensure_lanes_layer()
        layer = self.viewer.layers[self._LANES_LAYER]

        rects = lanes_to_napari_rects(self.lanes)
        self._updating_lanes = True
        try:
            if not rects:
                layer.data = []
            else:
                edge_colors, face_colors = lane_colors_for_napari(self.lanes)
                props = build_lane_properties(self.lanes)

                layer.data = rects
                layer.edge_color = edge_colors
                layer.face_color = face_colors
                layer.properties = props
        finally:
            self._updating_lanes = False

    def _sync_lanes_from_layer(self) -> None:
        """Update ``self.lanes`` from the current Shapes layer data.

        Called before analysis to pick up any manually drawn rectangles.
        """
        from gel_boy.gui.napari_utils import napari_rect_to_lane_coords
        from gel_boy.models.lane import Lane

        if self._LANES_LAYER not in self.viewer.layers:
            return

        arr = self._get_image_array()
        img_height = arr.shape[0] if arr is not None else 0

        layer = self.viewer.layers[self._LANES_LAYER]
        props = layer.properties or {}
        labels = props.get("label", [])

        self.lanes = []
        for i, rect in enumerate(layer.data):
            x_pos, width, y_start, y_end = napari_rect_to_lane_coords(rect)
            label = labels[i] if i < len(labels) else f"Lane {i + 1}"
            self.lanes.append(
                Lane(
                    x_position=x_pos,
                    width=width,
                    height=img_height,
                    label=label,
                    y_start=y_start,
                    y_end=y_end,
                )
            )

    # ------------------------------------------------------------------
    # Intensity profile analysis
    # ------------------------------------------------------------------

    def calculate_profiles(
        self,
        method: str = "mean",
        smooth_window: int = 5,
    ) -> None:
        """Extract and display intensity profiles for all defined lanes.

        Uses :func:`gel_boy.core.intensity_analysis.extract_lane_profile`
        and :func:`gel_boy.core.intensity_analysis.smooth_profile` unchanged.

        Args:
            method: Aggregation method - ``"mean"`` or ``"median"``.
            smooth_window: Moving-average window size for smoothing.
        """
        from gel_boy.core.intensity_analysis import (
            extract_lane_profile,
            smooth_profile,
        )

        self._sync_lanes_from_layer()
        arr = self._get_image_array()
        if arr is None or not self.lanes:
            return

        self._profiles = []
        img_height = arr.shape[0]
        for lane in self.lanes:
            # Always extract from the full image height so the underlying
            # algorithm sees the complete column; then slice to the lane's
            # y_start/y_end ROI afterwards to avoid off-by-one issues.
            profile = extract_lane_profile(
                arr,
                x_position=lane.x_position,
                width=lane.width,
                height=img_height,
                method=method,
            )
            if smooth_window > 1:
                profile = smooth_profile(profile, window_size=smooth_window)
            # Crop to the lane's ROI (y_start:y_end)
            roi_profile = profile[lane.y_start:lane.y_end]
            lane.set_intensity_profile(roi_profile, profile_type=method)
            self._profiles.append(roi_profile)

        self._plot_profiles()

    def _plot_profiles(self) -> None:
        """Open a matplotlib window with all lane intensity profiles."""
        import matplotlib.pyplot as plt

        if not self._profiles:
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        for i, (profile, lane) in enumerate(zip(self._profiles, self.lanes)):
            label = lane.label or f"Lane {i + 1}"
            color = [c / 255.0 for c in lane.color]
            ax.plot(profile, label=label, color=color, linewidth=1.5)

        ax.set_xlabel("Position (pixels)")
        ax.set_ylabel("Intensity")
        ax.set_title("Gel_Boy — Intensity Profiles")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        plt.show(block=False)

    # ------------------------------------------------------------------
    # Peak integration
    # ------------------------------------------------------------------

    def integrate_peaks(
        self,
        height_threshold: float = 0.05,
        min_distance: int = 10,
    ) -> None:
        """Detect and integrate peaks in the stored intensity profiles.

        Uses :func:`gel_boy.core.intensity_analysis.integrate_peak` together
        with ``scipy.signal.find_peaks`` for peak detection.

        Args:
            height_threshold: Fractional peak height threshold (0–1).
            min_distance: Minimum pixel distance between consecutive peaks.
        """
        from scipy.signal import find_peaks
        from gel_boy.core.intensity_analysis import integrate_peak

        if not self._profiles:
            self.calculate_profiles()

        results = []
        for i, (profile, lane) in enumerate(zip(self._profiles, self.lanes)):
            if profile.size == 0:
                continue

            norm = profile / profile.max() if profile.max() > 0 else profile
            peak_indices, _ = find_peaks(
                norm,
                height=height_threshold,
                distance=min_distance,
            )

            lane_results = []
            for peak_idx in peak_indices:
                half_dist = max(1, min_distance // 2)
                start = max(0, peak_idx - half_dist)
                end = min(len(profile), peak_idx + half_dist)
                area = integrate_peak(profile, start, end)
                lane_results.append((peak_idx, area))

            results.append((lane.label or f"Lane {i + 1}", lane_results))

        self._print_integration_results(results)

    @staticmethod
    def _print_integration_results(results: list) -> None:
        """Print peak integration results to stdout."""
        print("\n=== Peak Integration Results ===")
        for lane_label, peaks in results:
            print(f"\n{lane_label}:")
            if not peaks:
                print("  No peaks found.")
            for j, (pos, area) in enumerate(peaks, start=1):
                print(f"  Peak {j}: position={pos}px, area={area:.2f}")
        print("================================\n")

    # ------------------------------------------------------------------
    # Image operations
    # ------------------------------------------------------------------

    def apply_image_operation(self, operation: str) -> None:
        """Apply a named image operation to the loaded gel image.

        Uses functions from :mod:`gel_boy.core.image_processing` unchanged.
        Operations are applied to ``_current_pil_image`` (the last-transformed
        state).  *Reset Image* restores ``_original_pil_image`` (the image as
        it was first loaded).

        Args:
            operation: One of the operation name strings defined in
                       :func:`gel_boy.gui.napari_widgets.make_image_ops_widget`.
        """
        from gel_boy.core.image_processing import (
            rotate_image,
            flip_image,
            invert_image,
        )
        from gel_boy.gui.napari_utils import pil_image_to_numpy

        if self._original_pil_image is None:
            return

        _rotation_angles = {
            "Rotate CW 90°": -90,
            "Rotate CCW 90°": 90,
            "Rotate 180°": 180,
        }

        if operation == "Reset Image":
            self._current_pil_image = self._original_pil_image
        elif operation in _rotation_angles:
            img = rotate_image(self._current_pil_image, _rotation_angles[operation])
            self._current_pil_image = img
        elif operation == "Flip Horizontal":
            self._current_pil_image = flip_image(self._current_pil_image, horizontal=True)
        elif operation == "Flip Vertical":
            self._current_pil_image = flip_image(self._current_pil_image, horizontal=False)
        elif operation == "Invert Colors":
            self._current_pil_image = invert_image(self._current_pil_image)
        else:
            return

        self._set_image_data(pil_image_to_numpy(self._current_pil_image))

    def apply_rotation_precise(self, angle: float, expand: bool = False) -> None:
        """Rotate the current image by an arbitrary angle.

        Args:
            angle: Rotation angle in degrees (positive = counter-clockwise).
            expand: If ``True``, the canvas is expanded to fit the full
                    rotated image; otherwise the output is cropped to the
                    original dimensions.
        """
        from gel_boy.core.image_processing import rotate_image_precise
        from gel_boy.gui.napari_utils import pil_image_to_numpy

        if self._current_pil_image is None:
            return

        img = rotate_image_precise(self._current_pil_image, angle, expand=expand)
        self._current_pil_image = img
        self._set_image_data(pil_image_to_numpy(img))

    # ------------------------------------------------------------------
    # Application lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the napari event loop (blocking)."""
        import napari

        napari.run()
