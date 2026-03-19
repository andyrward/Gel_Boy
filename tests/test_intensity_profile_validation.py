"""Validation tests for intensity profile extraction using synthetic gel images.

These tests create images with *known* intensity profiles so we can verify
that the core extraction algorithm returns the expected values.  They serve
as a regression baseline independent of any GUI coordinate transformations.
"""

import numpy as np
import pytest

from gel_boy.core.intensity_analysis import (
    extract_lane_profile,
    calculate_profile_statistics,
)
from gel_boy.models.lane import Lane


# ---------------------------------------------------------------------------
# Synthetic image helpers
# ---------------------------------------------------------------------------

def create_linear_gradient_gel(
    width: int = 200,
    height: int = 100,
    lane_width: int = 20,
    lane_center: int = 100,
    v_start: float = 50.0,
    v_mid: float = 200.0,
    v_end: float = 50.0,
    background: int = 30,
) -> tuple:
    """Create a grayscale gel image with a linear gradient inside a lane.

    The lane runs from *v_start* at row 0, ramps up to *v_mid* at the
    midpoint and back down to *v_end* at the last row.  Pixels outside the
    lane region are set to *background*.

    Returns:
        (img_array, expected_profile) where *img_array* is a (height × width)
        uint8 numpy array and *expected_profile* is the float64 1-D array we
        expect ``extract_lane_profile`` to return.
    """
    mid = height // 2
    expected_profile = np.empty(height, dtype=np.float64)
    expected_profile[:mid] = np.linspace(v_start, v_mid, mid)
    expected_profile[mid:] = np.linspace(v_mid, v_end, height - mid)

    img = np.full((height, width), background, dtype=np.uint8)
    x_start = lane_center - lane_width // 2
    x_end = lane_center + lane_width // 2
    for y in range(height):
        img[y, x_start:x_end] = int(expected_profile[y])

    return img, expected_profile


def create_gaussian_peak_gel(
    width: int = 200,
    height: int = 100,
    lane_width: int = 20,
    lane_center: int = 100,
    peak_row: int = 50,
    amplitude: float = 180.0,
    baseline: float = 30.0,
    sigma: float = 10.0,
) -> tuple:
    """Create a grayscale gel image with a Gaussian intensity peak.

    Returns:
        (img_array, expected_profile)
    """
    rows = np.arange(height, dtype=np.float64)
    expected_profile = baseline + amplitude * np.exp(
        -((rows - peak_row) ** 2) / (2 * sigma ** 2)
    )

    img = np.full((height, width), int(baseline), dtype=np.uint8)
    x_start = lane_center - lane_width // 2
    x_end = lane_center + lane_width // 2
    for y in range(height):
        img[y, x_start:x_end] = int(expected_profile[y])

    return img, expected_profile


def create_two_lane_gel(
    width: int = 300,
    height: int = 100,
    lane_width: int = 20,
) -> tuple:
    """Create a gel with two distinct constant-intensity lanes.

    Returns:
        (img_array, center1, value1, center2, value2)
    """
    img = np.zeros((height, width), dtype=np.uint8)

    center1, value1 = 75, 100
    center2, value2 = 225, 150

    x1s = center1 - lane_width // 2
    img[:, x1s:x1s + lane_width] = value1

    x2s = center2 - lane_width // 2
    img[:, x2s:x2s + lane_width] = value2

    return img, center1, value1, center2, value2


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIntensityProfileValidation:
    """Validate profile extraction with synthetic images of known content."""

    def test_linear_gradient_mean_profile(self):
        """Mean profile extracted from a lane matches a known linear gradient."""
        img, expected = create_linear_gradient_gel(
            width=200, height=100, lane_width=20, lane_center=100
        )

        profile = extract_lane_profile(img, x_position=100, width=20, method='mean')

        assert profile.shape == (100,), f"Expected shape (100,), got {profile.shape}"
        np.testing.assert_allclose(
            profile, expected, rtol=0.02, atol=2.0,
            err_msg="Mean profile does not match the expected linear gradient",
        )

    def test_gaussian_peak_mean_profile(self):
        """Mean profile extracted from a Gaussian-peak lane matches expected."""
        img, expected = create_gaussian_peak_gel(
            width=200, height=100, lane_width=20, lane_center=100, peak_row=50
        )

        profile = extract_lane_profile(img, x_position=100, width=20, method='mean')

        assert profile.shape == (100,)
        np.testing.assert_allclose(profile, expected, rtol=0.02, atol=2.0)

    def test_cropped_roi_profile(self):
        """Profile extracted from a vertically-cropped ROI matches that slice."""
        img, expected_full = create_linear_gradient_gel(
            width=200, height=100, lane_width=20, lane_center=100
        )

        crop_y_start, crop_y_end = 20, 80
        roi = img[crop_y_start:crop_y_end, :]
        expected_cropped = expected_full[crop_y_start:crop_y_end]

        profile = extract_lane_profile(roi, x_position=100, width=20, method='mean')

        assert profile.shape == expected_cropped.shape, (
            f"Expected shape {expected_cropped.shape}, got {profile.shape}"
        )
        np.testing.assert_allclose(profile, expected_cropped, rtol=0.02, atol=2.0)

    def test_profile_statistics_keys_and_values(self):
        """calculate_profile_statistics returns correct keys and mean values."""
        img, expected = create_linear_gradient_gel()

        stats = calculate_profile_statistics(img, x_position=100, width=20)

        for key in ('mean_profile', 'median_profile', 'std_profile', 'background'):
            assert key in stats, f"Missing key: {key}"

        np.testing.assert_allclose(
            stats['mean_profile'], expected, rtol=0.02, atol=2.0,
        )

    def test_multiple_lanes_independent_profiles(self):
        """Profiles for two lanes in the same image are extracted independently."""
        img, c1, v1, c2, v2 = create_two_lane_gel(width=300, height=100)

        profile1 = extract_lane_profile(img, x_position=c1, width=20, method='mean')
        profile2 = extract_lane_profile(img, x_position=c2, width=20, method='mean')

        assert np.mean(profile1) == pytest.approx(v1, abs=1.0), (
            f"Lane 1 mean={np.mean(profile1):.2f}, expected {v1}"
        )
        assert np.mean(profile2) == pytest.approx(v2, abs=1.0), (
            f"Lane 2 mean={np.mean(profile2):.2f}, expected {v2}"
        )

    def test_lane_at_left_edge(self):
        """Profile extraction works for a lane whose left boundary is clamped."""
        img, _ = create_linear_gradient_gel(width=200, height=100)

        profile = extract_lane_profile(img, x_position=5, width=20, method='mean')

        assert len(profile) == 100

    def test_lane_at_right_edge(self):
        """Profile extraction works for a lane whose right boundary is clamped."""
        img, _ = create_linear_gradient_gel(width=200, height=100)

        profile = extract_lane_profile(img, x_position=195, width=20, method='mean')

        assert len(profile) == 100

    def test_median_profile_matches_mean_for_uniform_lane(self):
        """Mean and median profiles are identical for a uniform-intensity lane."""
        img = np.zeros((100, 200), dtype=np.uint8)
        img[:, 90:110] = 128  # uniform lane

        mean_p = extract_lane_profile(img, x_position=100, width=20, method='mean')
        median_p = extract_lane_profile(img, x_position=100, width=20, method='median')

        np.testing.assert_allclose(mean_p, median_p)

    def test_profile_length_matches_roi_height(self):
        """Profile length equals the number of rows in the provided image/ROI."""
        for roi_height in (30, 50, 80, 100):
            img = np.ones((roi_height, 200), dtype=np.uint8) * 100
            profile = extract_lane_profile(img, x_position=100, width=20)
            assert len(profile) == roi_height, (
                f"Profile length {len(profile)} != ROI height {roi_height}"
            )

    def test_lane_model_roi_clamping_in_profile_calculation(self):
        """Negative y_start / oversized y_end are clamped before slicing."""
        img = np.full((100, 200), 128, dtype=np.uint8)
        img_height = img.shape[0]

        # Simulate a lane with out-of-bound y coordinates
        lane = Lane(x_position=100, width=20, height=150, y_start=-10, y_end=200)

        y_start = max(0, min(lane.y_start, img_height))
        y_end = max(y_start, min(lane.y_end, img_height))

        if y_start >= y_end:
            roi = img
        else:
            roi = img[y_start:y_end, :]

        stats = calculate_profile_statistics(roi, lane.x_position, lane.width)

        # Profile must be non-empty and match the clamped height
        assert len(stats['mean_profile']) > 0
        np.testing.assert_allclose(stats['mean_profile'], 128.0, atol=1.0)
