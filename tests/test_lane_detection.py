"""Tests for lane detection algorithms."""

import numpy as np
from gel_boy.core.lane_detection import detect_lanes, refine_lane_boundaries, validate_lanes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_gel_image(
    width: int = 400,
    height: int = 100,
    lane_centers: list = None,
    lane_widths: list = None,
    background: int = 20,
    lane_intensity: int = 200,
) -> np.ndarray:
    """Create a synthetic grayscale gel image with vertical lane stripes."""
    img = np.full((height, width), background, dtype=np.uint8)
    if lane_centers is None:
        return img
    if lane_widths is None:
        lane_widths = [30] * len(lane_centers)
    for center, w in zip(lane_centers, lane_widths):
        left = max(0, center - w // 2)
        right = min(width, center + w // 2)
        img[:, left:right] = lane_intensity
    return img


# ---------------------------------------------------------------------------
# detect_lanes
# ---------------------------------------------------------------------------

class TestDetectLanes:

    def test_returns_list(self):
        """detect_lanes always returns a list."""
        img = np.zeros((50, 100), dtype=np.uint8)
        result = detect_lanes(img)
        assert isinstance(result, list)

    def test_empty_image_returns_empty(self):
        """detect_lanes returns empty list for blank image."""
        img = np.zeros((50, 100), dtype=np.uint8)
        result = detect_lanes(img)
        assert result == []

    def test_single_lane(self):
        """detect_lanes finds a single lane."""
        img = make_gel_image(width=200, lane_centers=[100], lane_widths=[40])
        result = detect_lanes(img, min_lane_width=20, max_lane_width=80)
        assert len(result) == 1

    def test_two_lanes(self):
        """detect_lanes finds two well-separated lanes."""
        img = make_gel_image(width=300, lane_centers=[75, 225], lane_widths=[40, 40])
        result = detect_lanes(img, min_lane_width=20, max_lane_width=80)
        assert len(result) == 2

    def test_multiple_lanes(self):
        """detect_lanes handles many lanes (e.g. 5)."""
        centers = [40, 100, 160, 220, 280]
        img = make_gel_image(width=320, lane_centers=centers, lane_widths=[25] * 5)
        result = detect_lanes(img, min_lane_width=10, max_lane_width=60)
        assert len(result) >= 4  # Allow minor detection errors at edges

    def test_min_width_filter(self):
        """detect_lanes respects min_lane_width."""
        # Very narrow stripe of width 5 — should be filtered out
        img = make_gel_image(width=200, lane_centers=[100], lane_widths=[5])
        result = detect_lanes(img, min_lane_width=20, max_lane_width=100)
        assert len(result) == 0

    def test_max_width_filter(self):
        """detect_lanes respects max_lane_width."""
        # Very wide stripe of width 180 — should be filtered out
        img = make_gel_image(width=200, lane_centers=[100], lane_widths=[180])
        result = detect_lanes(img, min_lane_width=20, max_lane_width=80)
        assert len(result) == 0

    def test_result_structure(self):
        """Each result is a (x_position, width) tuple of ints."""
        img = make_gel_image(width=200, lane_centers=[100], lane_widths=[40])
        result = detect_lanes(img, min_lane_width=20, max_lane_width=80)
        assert len(result) >= 1
        x_pos, width = result[0]
        assert isinstance(x_pos, int)
        assert isinstance(width, int)
        assert width > 0

    def test_rgb_image(self):
        """detect_lanes works with RGB images."""
        gray = make_gel_image(width=200, lane_centers=[100], lane_widths=[40])
        rgb = np.stack([gray, gray, gray], axis=2)
        result = detect_lanes(rgb, min_lane_width=20, max_lane_width=80)
        assert len(result) == 1

    def test_none_not_accepted(self):
        """detect_lanes returns empty list for None-like empty input."""
        result = detect_lanes(np.array([]), min_lane_width=20, max_lane_width=100)
        assert result == []


# ---------------------------------------------------------------------------
# refine_lane_boundaries
# ---------------------------------------------------------------------------

class TestRefineLaneBoundaries:

    def test_returns_same_count(self):
        """refine_lane_boundaries returns same number of lanes."""
        img = make_gel_image(width=300, lane_centers=[75, 225], lane_widths=[40, 40])
        initial = [(75, 40), (225, 40)]
        refined = refine_lane_boundaries(img, initial)
        assert len(refined) == len(initial)

    def test_empty_initial_returns_empty(self):
        """Empty initial lanes → empty result."""
        img = make_gel_image(width=200, lane_centers=[100], lane_widths=[40])
        result = refine_lane_boundaries(img, [])
        assert result == []

    def test_result_structure(self):
        """Each result is a (x_position, width) tuple."""
        img = make_gel_image(width=200, lane_centers=[100], lane_widths=[40])
        refined = refine_lane_boundaries(img, [(100, 40)])
        assert len(refined) == 1
        x, w = refined[0]
        assert isinstance(x, int)
        assert isinstance(w, int)
        assert w > 0

    def test_single_lane_reasonable_bounds(self):
        """Refined center should stay within expected range."""
        img = make_gel_image(width=200, lane_centers=[100], lane_widths=[40])
        refined = refine_lane_boundaries(img, [(100, 40)])
        x, w = refined[0]
        # Center should still be within ±30 pixels of original
        assert abs(x - 100) <= 30


# ---------------------------------------------------------------------------
# validate_lanes
# ---------------------------------------------------------------------------

class TestValidateLanes:

    def test_empty_lanes_valid(self):
        """No lanes is always valid."""
        assert validate_lanes([], image_width=200) is True

    def test_valid_single_lane(self):
        """Single lane within bounds is valid."""
        assert validate_lanes([(100, 40)], image_width=200) is True

    def test_valid_multiple_lanes(self):
        """Multiple non-overlapping lanes within bounds are valid."""
        assert validate_lanes([(50, 30), (150, 30)], image_width=200) is True

    def test_lane_out_of_bounds_left(self):
        """Lane extending past left edge is invalid."""
        assert validate_lanes([(5, 40)], image_width=200) is False

    def test_lane_out_of_bounds_right(self):
        """Lane extending past right edge is invalid."""
        assert validate_lanes([(190, 40)], image_width=200) is False

    def test_overlapping_lanes_invalid(self):
        """Overlapping lanes are invalid."""
        # Lanes at 50±20 and 60±20 overlap
        assert validate_lanes([(50, 40), (60, 40)], image_width=200) is False

    def test_zero_width_invalid(self):
        """Zero-width lane is invalid."""
        assert validate_lanes([(100, 0)], image_width=200) is False

    def test_negative_width_invalid(self):
        """Negative-width lane is invalid."""
        assert validate_lanes([(100, -5)], image_width=200) is False
