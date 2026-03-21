"""Integration tests for the napari-based Gel_Boy application.

These tests verify that the napari infrastructure wires correctly to the
existing core analysis modules without exercising the GUI event loop.
All tests use numpy arrays directly, so no display/Qt environment is needed.
"""

from __future__ import annotations

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_gel_image(height: int = 100, width: int = 200) -> np.ndarray:
    """Return a synthetic 8-bit grayscale gel image with two bright lanes."""
    img = np.zeros((height, width), dtype=np.uint8)
    img[:, 40:80] = 200   # lane 1
    img[:, 120:160] = 180  # lane 2
    return img


# ---------------------------------------------------------------------------
# napari_utils tests
# ---------------------------------------------------------------------------

class TestNapariUtils:
    """Tests for coordinate conversion helpers."""

    def test_lane_to_napari_rect_shape(self):
        from gel_boy.gui.napari_utils import lane_to_napari_rect
        from gel_boy.models.lane import Lane

        lane = Lane(x_position=60, width=40, height=100, y_start=0, y_end=100)
        rect = lane_to_napari_rect(lane)
        assert rect.shape == (4, 2), "Rectangle must have 4 corner points in (y, x) format"

    def test_lane_to_napari_rect_coords(self):
        from gel_boy.gui.napari_utils import lane_to_napari_rect
        from gel_boy.models.lane import Lane

        lane = Lane(x_position=60, width=40, height=100, y_start=10, y_end=90)
        rect = lane_to_napari_rect(lane)
        y_vals = rect[:, 0]
        x_vals = rect[:, 1]
        assert y_vals.min() == pytest.approx(10.0)
        assert y_vals.max() == pytest.approx(90.0)
        assert x_vals.min() == pytest.approx(lane.x_start)
        assert x_vals.max() == pytest.approx(lane.x_end)

    def test_napari_rect_to_lane_coords_roundtrip(self):
        from gel_boy.gui.napari_utils import lane_to_napari_rect, napari_rect_to_lane_coords
        from gel_boy.models.lane import Lane

        lane = Lane(x_position=60, width=40, height=100, y_start=5, y_end=95)
        rect = lane_to_napari_rect(lane)
        x_pos, width, y_start, y_end = napari_rect_to_lane_coords(rect)

        assert x_pos == lane.x_position
        assert width == lane.width
        assert y_start == lane.y_start
        assert y_end == lane.y_end

    def test_pil_image_to_numpy_8bit_grayscale(self):
        from PIL import Image
        from gel_boy.gui.napari_utils import pil_image_to_numpy

        pil = Image.fromarray(np.full((50, 100), 128, dtype=np.uint8), mode="L")
        arr = pil_image_to_numpy(pil)
        assert arr.dtype == np.uint8
        assert arr.shape == (50, 100)
        assert arr[0, 0] == 128

    def test_pil_image_to_numpy_rgb(self):
        from PIL import Image
        from gel_boy.gui.napari_utils import pil_image_to_numpy

        data = np.zeros((50, 100, 3), dtype=np.uint8)
        data[:, :, 0] = 255  # red channel
        pil = Image.fromarray(data, mode="RGB")
        arr = pil_image_to_numpy(pil)
        assert arr.shape == (50, 100, 3)
        assert arr[0, 0, 0] == 255

    def test_lanes_to_napari_rects_length(self):
        from gel_boy.gui.napari_utils import lanes_to_napari_rects
        from gel_boy.models.lane import Lane

        lanes = [
            Lane(x_position=60, width=40, height=100),
            Lane(x_position=140, width=40, height=100),
        ]
        rects = lanes_to_napari_rects(lanes)
        assert len(rects) == 2

    def test_lane_colors_for_napari(self):
        from gel_boy.gui.napari_utils import lane_colors_for_napari
        from gel_boy.models.lane import Lane

        lanes = [Lane(x_position=60, width=40, height=100, color=(0, 120, 215))]
        edge, face = lane_colors_for_napari(lanes)
        assert len(edge) == 1
        assert len(face) == 1
        # Edge alpha should be 1.0
        assert edge[0][3] == pytest.approx(1.0)

    def test_build_lane_properties(self):
        from gel_boy.gui.napari_utils import build_lane_properties
        from gel_boy.models.lane import Lane

        lanes = [
            Lane(x_position=60, width=40, height=100, label="Ladder"),
            Lane(x_position=140, width=40, height=100, label=""),
        ]
        props = build_lane_properties(lanes)
        assert props["label"][0] == "Ladder"
        assert props["label"][1] == "Lane 2"


# ---------------------------------------------------------------------------
# napari_main logic tests (no viewer instantiation needed)
# ---------------------------------------------------------------------------

class TestGelBoyNapariAppLogic:
    """Tests for GelBoyNapariApp methods that don't require a running viewer."""

    def test_print_integration_results_no_error(self, capsys):
        from gel_boy.gui.napari_main import GelBoyNapariApp

        results = [
            ("Lane 1", [(10, 500.5), (40, 300.2)]),
            ("Lane 2", []),
        ]
        GelBoyNapariApp._print_integration_results(results)
        captured = capsys.readouterr()
        assert "Lane 1" in captured.out
        assert "Peak 1" in captured.out
        assert "No peaks found" in captured.out

    def test_print_integration_results_empty(self, capsys):
        from gel_boy.gui.napari_main import GelBoyNapariApp

        GelBoyNapariApp._print_integration_results([])
        captured = capsys.readouterr()
        assert "Peak Integration Results" in captured.out


# ---------------------------------------------------------------------------
# main.py entry-point smoke test
# ---------------------------------------------------------------------------

class TestMainEntryPoint:
    """Verify main.py wires correctly without launching a viewer."""

    def test_main_module_importable(self):
        """main.py must be importable without side effects."""
        import importlib
        import importlib.util
        from pathlib import Path

        main_path = Path(__file__).parent.parent / "main.py"
        spec = importlib.util.spec_from_file_location(
            "gel_boy_main",
            str(main_path),
        )
        mod = importlib.util.module_from_spec(spec)
        # Just loading the module (without calling main()) should not raise.
        spec.loader.exec_module(mod)
        assert hasattr(mod, "main")
        assert hasattr(mod, "_run_napari")
        assert hasattr(mod, "_run_legacy")
