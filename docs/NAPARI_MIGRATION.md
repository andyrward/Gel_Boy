# Napari Migration Guide

## Overview

Gel_Boy 0.2.0 migrates from a custom PyQt6 `QGraphicsView`-based image
viewer to [napari](https://napari.org) as the primary display backend.
All gel-specific analysis algorithms (`intensity_analysis`, `lane_detection`,
`image_processing`, the `Lane` model, etc.) are **unchanged** — only the GUI
layer has been replaced.

## Why napari?

| | **napari viewer (Gel_Boy v0.2.0)** | **PyQt6 QGraphicsView (Gel_Boy v0.1.x)** |
|---|---|---|
| Coordinate handling | ✅ Automatic | ❌ Manual, caused ROI bugs |
| Image display | ✅ N-D, multi-layer | Custom, 2-D only |
| Lane overlay | ✅ Shapes layer | Custom paint overlay |
| Extensibility | Plugin system | Custom code |
| Your analysis code | 100% preserved | 100% preserved |

## New Files

| File | Purpose |
|---|---|
| `gel_boy/gui/napari_main.py` | `GelBoyNapariApp` — main application class |
| `gel_boy/gui/napari_widgets.py` | `magicgui` dock-widget factories |
| `gel_boy/gui/napari_utils.py` | Coordinate conversion helpers |
| `tests/test_napari_integration.py` | Integration tests |

## Deprecated (kept for reference, not imported by default)

- `gel_boy/gui/main_window.py`
- `gel_boy/gui/widgets/image_viewer.py`
- `gel_boy/gui/widgets/lane_panel.py`
- `gel_boy/gui/widgets/side_panel.py`
- `gel_boy/gui/widgets/lane_overlay.py`

## Installation

```bash
# Install with uv (recommended)
uv pip install -e .

# Install with pip
pip install -e .
```

The new `pyproject.toml` pulls in `napari[all]`, `magicgui`, `scikit-image`,
and `scipy` automatically.  PyQt6 is no longer a direct dependency but is
available as the optional `legacy` extra if needed:

```bash
pip install -e ".[legacy]"
```

## Running the Application

### Default (napari viewer)

```bash
python main.py
```

### Legacy PyQt6 interface (deprecated)

```bash
python main.py --legacy
```

## Workflow in the New Interface

1. **Load an image** — drag a gel image onto the napari canvas, or use
   `File → Open…` from the napari menu.

2. **Detect lanes automatically** — expand the *Lane Detection* dock
   widget on the right, set min/max lane width, and click **Detect Lanes**
   (or press `Ctrl+L`).

3. **Draw lanes manually** — press `D` to enter rectangle-drawing mode on
   the *Lanes* layer, then click-and-drag to define a lane.

4. **Calculate profiles** — expand the *Intensity Profiles* dock widget,
   choose aggregation method and smoothing, then click **Calculate Profiles**
   (or press `Ctrl+P`).  A matplotlib window opens with all lane profiles.

5. **Integrate peaks** — expand the *Peak Integration* dock widget, adjust
   height threshold and minimum distance, then click **Integrate Peaks**.
   Results are printed to the console.

6. **Image operations** — use the *Image Operations* dock widget (left side)
   to rotate, flip, invert, or reset the gel image.

## Coordinate System

napari uses **(row, col)** = **(y, x)** ordering for all layer data.
The `napari_utils` module provides conversion helpers:

```python
from gel_boy.gui.napari_utils import lane_to_napari_rect, napari_rect_to_lane_coords

# Lane → napari rectangle
rect = lane_to_napari_rect(lane)   # (4, 2) array in (y, x) order

# napari rectangle → lane coordinates
x_pos, width, y_start, y_end = napari_rect_to_lane_coords(rect)
```

## API Compatibility

The core analysis API is **identical** to v0.1.x:

```python
from gel_boy.core.intensity_analysis import extract_lane_profile
from gel_boy.core.lane_detection import detect_lanes
from gel_boy.core.image_processing import rotate_image, flip_image, invert_image
from gel_boy.models.lane import Lane
```

All existing unit tests continue to pass without modification.

## Programmatic Usage

```python
from gel_boy.gui.napari_main import GelBoyNapariApp

app = GelBoyNapariApp()
app.load_image("my_gel.tif")   # load a gel image
app.detect_lanes()              # auto-detect lanes
app.calculate_profiles()        # extract + plot profiles
app.run()                       # start the event loop
```
