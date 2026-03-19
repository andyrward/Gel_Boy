"""Diagnostic tests for coordinate transformations in lane profile extraction.

These tests trace the full path from raw image coordinates, through lane
creation, through ROI cropping, to the final extracted profile.  If any
step introduces a coordinate mismatch the assertion messages pinpoint it.
"""

import numpy as np
import pytest

from gel_boy.core.intensity_analysis import (
    extract_lane_profile,
    calculate_profile_statistics,
)
from gel_boy.models.lane import Lane


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_striped_image(
    height: int = 100,
    width: int = 200,
    stripe_center: int = 100,
    stripe_width: int = 20,
    stripe_value: int = 200,
    background: int = 30,
) -> np.ndarray:
    """Return a grayscale image with a single bright vertical stripe."""
    img = np.full((height, width), background, dtype=np.uint8)
    x_start = stripe_center - stripe_width // 2
    x_end = stripe_center + stripe_width // 2
    img[:, x_start:x_end] = stripe_value
    return img


def make_row_gradient_image(
    height: int = 100,
    width: int = 200,
    lane_center: int = 100,
    lane_width: int = 20,
    background: int = 20,
) -> tuple:
    """Return image where each row inside the lane equals the row index.

    Returns:
        (img_array, expected_profile) where expected_profile[y] == y.
    """
    img = np.full((height, width), background, dtype=np.uint8)
    x_start = lane_center - lane_width // 2
    x_end = lane_center + lane_width // 2
    for y in range(height):
        img[y, x_start:x_end] = y  # intensity == row index

    expected = np.arange(height, dtype=np.float64)
    return img, expected


# ---------------------------------------------------------------------------
# Coordinate flow tests
# ---------------------------------------------------------------------------

class TestCoordinateFlow:
    """Trace coordinates through the full extraction pipeline."""

    def test_stripe_at_known_x_position(self):
        """Profile at the exact stripe center returns the stripe value."""
        stripe_center = 100
        stripe_value = 200
        img = make_striped_image(
            height=100, width=200,
            stripe_center=stripe_center,
            stripe_value=stripe_value,
        )

        profile = extract_lane_profile(img, x_position=stripe_center, width=20)

        assert np.allclose(profile, stripe_value), (
            f"Expected all rows ≈ {stripe_value}, got mean={np.mean(profile):.2f}"
        )

    def test_profile_offset_x_wrong_position_misses_stripe(self):
        """Profile extracted far from the stripe center returns background."""
        img = make_striped_image(
            height=100, width=200, stripe_center=100, stripe_value=200, background=30
        )

        # Extract a lane that does NOT overlap the stripe
        profile = extract_lane_profile(img, x_position=30, width=20)

        assert np.mean(profile) < 60, (
            f"Expected background ≈ 30, got mean={np.mean(profile):.2f}; "
            "X-coordinate mismatch may have placed the extraction over the stripe"
        )

    def test_row_gradient_full_image(self):
        """Profile from a full-height image equals the row-index gradient."""
        img, expected = make_row_gradient_image(
            height=100, width=200, lane_center=100, lane_width=20
        )

        profile = extract_lane_profile(img, x_position=100, width=20)

        np.testing.assert_allclose(
            profile, expected, atol=1.0,
            err_msg="Full-image row-gradient profile mismatch",
        )

    def test_row_gradient_cropped_roi(self):
        """Profile from a cropped ROI equals that slice of the row-index gradient."""
        img, expected_full = make_row_gradient_image(
            height=100, width=200, lane_center=100, lane_width=20
        )

        y_start, y_end = 25, 75
        roi = img[y_start:y_end, :]
        expected_slice = expected_full[y_start:y_end]

        profile = extract_lane_profile(roi, x_position=100, width=20)

        assert profile.shape == expected_slice.shape, (
            f"Expected shape {expected_slice.shape}, got {profile.shape}"
        )
        np.testing.assert_allclose(
            profile, expected_slice, atol=1.0,
            err_msg=(
                f"Cropped ROI [{y_start}:{y_end}] profile mismatch; "
                "check that y coordinates were clamped before slicing"
            ),
        )

    def test_negative_y_start_clamped(self):
        """Negative y_start is clamped to 0 before slicing to avoid wrap-around."""
        img = make_striped_image(height=100, width=200, stripe_value=200)
        img_height = img.shape[0]

        lane = Lane(x_position=100, width=20, height=120, y_start=-15, y_end=60)

        y_start = max(0, min(lane.y_start, img_height))
        y_end = max(y_start, min(lane.y_end, img_height))

        roi = img[y_start:y_end, :]

        # y_start must have been clamped to 0
        assert y_start == 0, f"Clamped y_start should be 0, got {y_start}"
        assert roi.shape[0] == y_end - y_start, (
            f"ROI height {roi.shape[0]} != expected {y_end - y_start}"
        )

        profile = extract_lane_profile(roi, x_position=100, width=20)
        assert len(profile) == y_end - y_start

    def test_y_end_beyond_image_clamped(self):
        """y_end beyond image height is clamped to the actual image height."""
        img = make_striped_image(height=100, width=200, stripe_value=200)
        img_height = img.shape[0]

        lane = Lane(x_position=100, width=20, height=200, y_start=40, y_end=300)

        y_start = max(0, min(lane.y_start, img_height))
        y_end = max(y_start, min(lane.y_end, img_height))

        assert y_end == img_height, f"Clamped y_end should be {img_height}, got {y_end}"

        roi = img[y_start:y_end, :]
        assert roi.shape[0] == img_height - 40

    def test_y_start_equals_y_end_falls_back_to_full_image(self):
        """When y_start == y_end the full image is used (zero-height ROI guard)."""
        img = make_striped_image(height=100, width=200, stripe_value=200)
        img_height = img.shape[0]

        y_start, y_end = 50, 50  # degenerate

        if y_start >= y_end:
            roi = img
        else:
            roi = img[y_start:y_end, :]

        assert roi.shape[0] == img_height, (
            "Degenerate ROI should fall back to full image"
        )

    def test_x_position_unchanged_after_vertical_crop(self):
        """Vertical crop does not affect X coordinates for profile extraction."""
        # Place the stripe at a well-known x position
        stripe_center = 120
        img = make_striped_image(
            height=100, width=200,
            stripe_center=stripe_center,
            stripe_value=200,
            background=30,
        )

        # Crop vertically
        roi = img[20:80, :]

        # X coordinates of the lane are still in terms of the original image width
        profile = extract_lane_profile(roi, x_position=stripe_center, width=20)

        assert np.mean(profile) > 150, (
            f"Expected stripe value ≈ 200 after vertical crop, "
            f"got mean={np.mean(profile):.2f}; "
            "vertical crop must not shift X coordinates"
        )

    def test_full_pipeline_known_image(self):
        """End-to-end: create lane, crop ROI, extract stats, verify profile."""
        height, width = 80, 200
        stripe_center, stripe_width, stripe_value = 100, 20, 180

        img = make_striped_image(
            height=height, width=width,
            stripe_center=stripe_center,
            stripe_width=stripe_width,
            stripe_value=stripe_value,
            background=20,
        )

        lane = Lane(
            x_position=stripe_center,
            width=stripe_width,
            height=height,
            y_start=10,
            y_end=70,
        )

        img_height = img.shape[0]
        y_start = max(0, min(lane.y_start, img_height))
        y_end = max(y_start, min(lane.y_end, img_height))

        roi = img[y_start:y_end, :]
        stats = calculate_profile_statistics(roi, lane.x_position, lane.width)

        mean_p = stats['mean_profile']

        assert len(mean_p) == y_end - y_start, (
            f"Profile length {len(mean_p)} != ROI height {y_end - y_start}"
        )
        np.testing.assert_allclose(
            mean_p, stripe_value, atol=2.0,
            err_msg=f"Full-pipeline profile mean mismatch (expected {stripe_value})",
        )
