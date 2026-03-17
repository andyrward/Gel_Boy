# Lane Analysis User Guide

This guide explains how to use the lane detection, manual lane drawing, and intensity profile visualization features in Gel_Boy.

---

## Overview

The lane analysis workflow consists of three main steps:

1. **Define lanes** — automatically or by hand
2. **Calculate intensity profiles** — mean or median aggregation across each lane
3. **Analyze profiles** — integrate peaks, subtract background, export results

---

## 1. Defining Lanes

### Automatic Detection (`Ctrl+L`)

1. Open a gel image (**File → Open Image…**).
2. Go to **Analysis → Detect Lanes** (or press `Ctrl+L`).
3. Gel_Boy projects the image horizontally (sums pixel values across all rows) and finds bright vertical bands.
4. Detected lanes appear as colored rectangles overlaid on the image and in the **Lanes** list in the side panel.

**Tuning detection:**  
Use the **Min W** and **Max W** spinboxes in the Lane Panel to filter lanes by width before running detection.

### Manual Drawing (`Ctrl+Shift+L`)

1. Click **Draw Lane** in the Lane Panel, or press `Ctrl+Shift+L`.  
   The cursor changes to a crosshair.
2. Click and drag on the image to draw a rectangle defining the lane boundaries.
3. Release the mouse to confirm the lane.
4. Press **Draw Lane** again (or `Ctrl+Shift+L`) to exit drawing mode.

### Editing Lanes

With the **Edit** mode enabled on the Lane Overlay:

| Action | Effect |
|--------|--------|
| Drag lane body | Reposition the entire lane |
| Drag left/right edge handle | Resize the lane width |
| Right-click lane | Open context menu (edit properties / delete) |

You can also adjust properties in the **Lane Properties** section of the side panel:

- **Label** — free text name for the lane
- **Width** — pixel width
- **Color** — click the color swatch to open the color picker

### Deleting Lanes

- Select a lane in the list and click **Delete**, or
- Right-click the lane on the image and choose **Delete Lane**, or
- Use **Analysis → Clear All Lanes** to remove every lane at once.

---

## 2. Intensity Profiles

### Calculating Profiles (`Ctrl+P`)

1. With lanes defined, click **Calculate Profiles** in the Lane Panel, or press `Ctrl+P`.
2. Choose **Mean** or **Median** aggregation:
   - **Mean** — average pixel intensity across the lane width at each row
   - **Median** — median pixel intensity across the lane width at each row (more robust to bright/dark streaks)
3. The intensity profiles appear in the **Intensity Profile** panel at the bottom of the window.

### Profile Display

The plot shows:
- X axis: position along the lane (pixels from top)
- Y axis: intensity value
- One colored line per lane (colors match lane rectangles)
- A grid and legend for easy reading

**Navigation:** Use the matplotlib toolbar (zoom, pan, home, save) just above the plot.

### Smoothing

Adjust the **Smoothing** slider to apply a moving-average filter to the profiles. A window of 1 means no smoothing. Higher values reduce noise but may merge closely spaced bands.

---

## 3. Peak Integration

### Selecting an Integration Region

1. In the **Mode** selector above the plot, choose **Integrate**.
2. Click and drag on the plot to draw a horizontal span over a band.
3. Release the mouse. The area is shaded and the integrated area is displayed as an annotation and added to the **Integration Results** table.

You can add multiple integration regions per lane. Each region stores:
- `raw_area` — trapezoid-rule integration of the raw profile
- `corrected_area` — integration after linear background subtraction (if background points are set)

### Clearing Integration Regions

Click **Clear Integrations** above the plot to remove all integration spans.

---

## 4. Background Correction

### Setting Background Points

1. In the **Mode** selector, choose **Background**.
2. Click on the plot at positions you know represent background (typically on either side of a band).
3. A marker (×) appears for each point.
4. Once two or more points are set, a dashed line shows the fitted linear background.

Background correction is applied automatically to any new integration regions. Existing regions are **not** retroactively updated — click **Clear Integrations** and re-select regions to refresh corrected areas.

### Removing Background Points

Click **Clear BG Points** to remove all background reference points.

---

## 5. Integration Results Table

The table below the plot shows all integration results with columns:

| Column | Description |
|--------|-------------|
| Lane | Lane label |
| Start | Start pixel index of the integration region |
| End | End pixel index |
| Raw Area | Area without background correction |
| Corrected Area | Area after linear background subtraction |

---

## 6. Exporting

### Export Plot

Click **Export Plot** above the plot to save the current view as a PNG or SVG file.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Auto-detect lanes |
| `Ctrl+Shift+L` | Toggle manual lane drawing mode |
| `Ctrl+P` | Calculate intensity profiles |

---

## Algorithm Details

### Lane Detection

1. Compute the vertical projection: sum each column of pixel values across all rows.
2. Apply a moving-average smoothing window (width ≈ ¼ of `min_lane_width`).
3. Normalize to [0, 1] and threshold at 0.3.
4. Find contiguous above-threshold regions as candidate lanes.
5. Filter by `min_lane_width` / `max_lane_width`.
6. Optional: refine boundaries using the gradient of the projection.

### Profile Extraction (`extract_lane_profile`)

```python
from gel_boy.core.intensity_analysis import extract_lane_profile

profile = extract_lane_profile(
    image=np_image,   # numpy array (H×W grayscale or H×W×3 RGB)
    x_position=100,   # lane center (pixels)
    width=40,         # lane width (pixels)
    method='mean',    # 'mean' or 'median'
)
# profile.shape == (image_height,)
```

### Peak Integration (`integrate_peak`)

```python
from gel_boy.core.intensity_analysis import integrate_peak

result = integrate_peak(
    profile=profile,
    start_idx=30,
    end_idx=70,
    background_points=[(10, 15.0), (80, 12.0)],  # optional
)
# result['corrected_area'] → float
```

### Background Subtraction (`subtract_linear_background`)

```python
from gel_boy.core.intensity_analysis import subtract_linear_background

bg_line, corrected, slope, intercept = subtract_linear_background(
    profile=profile,
    points=[(10, 15.0), (80, 12.0)],
)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No lanes detected | Lower the intensity threshold by adjusting Min/Max lane width, or use manual drawing |
| Too many lanes detected | Increase **Min W** or **Max W** to filter narrow/wide false positives |
| Profile looks noisy | Increase the **Smoothing** slider |
| Background correction line looks wrong | Add more background points spanning the full lane height |
