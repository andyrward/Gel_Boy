# Gel_Boy

A cross-platform gel electrophoresis image analysis and annotation tool built with Python and [napari](https://napari.org).

## Overview

Gel_Boy is a desktop application designed to help researchers analyze gel electrophoresis images with features for:

- **Lane Detection**: Automatically or manually define lanes in gel images
- **Band Detection**: Identify and quantify protein or DNA bands
- **Intensity Analysis**: Generate and analyze intensity profiles for each lane
- **Molecular Weight Calibration**: Calibrate using standard ladders for accurate MW estimation
- **Annotation**: Add labels, markers, and notes to gel images
- **Export**: Export results to CSV, Excel, and annotated images

## Features

- ✅ Cross-platform support (Windows, macOS, Linux)
- ✅ napari-powered viewer — robust coordinate handling, multi-layer display
- ✅ Support for common image formats (PNG, JPEG, TIFF, BMP) including 16-bit TIFF
- ✅ Automatic lane detection algorithms
- ✅ Interactive lane drawing and editing via napari Shapes layer
- ✅ Intensity profile extraction and visualization (matplotlib)
- ✅ Peak detection and integration (scipy)
- ✅ Band quantification and molecular weight estimation
- ✅ Project-based workflow with save/load functionality
- ✅ Multiple export formats for data and images
- ✅ Customizable image processing filters

## Installation

### Using uv (Recommended)

Gel_Boy uses [uv](https://github.com/astral-sh/uv) for fast, reliable dependency management.

1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/andyrward/Gel_Boy.git
   cd Gel_Boy
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Run the application:
   ```bash
   uv run python main.py
   ```

### Using pip

Alternatively, you can use pip:

```bash
pip install -e .
python main.py
```

## Quick Start

1. **Launch Gel_Boy**: Run `uv run python main.py`
2. **Load an Image**: Drag a gel image onto the napari canvas, or use `File → Open…`
3. **Detect Lanes**: Click **Detect Lanes** in the right dock widget (or press `Ctrl+L`)
4. **Draw Lanes Manually**: Press `D` to enter rectangle-drawing mode on the *Lanes* layer
5. **Calculate Profiles**: Click **Calculate Profiles** (or press `Ctrl+P`)
6. **Integrate Peaks**: Click **Integrate Peaks** in the *Peak Integration* dock widget
7. **Export Results**: Use napari's built-in export options, or File → Export from the menu

For detailed instructions, see the [User Guide](docs/user_guide.md) and the
[Napari Migration Guide](docs/NAPARI_MIGRATION.md).

## Development

### Project Structure

```
Gel_Boy/
├── gel_boy/           # Main package
│   ├── gui/          # GUI components
│   │   ├── napari_main.py    # GelBoyNapariApp (napari viewer)
│   │   ├── napari_widgets.py # magicgui dock widgets
│   │   ├── napari_utils.py   # Coordinate conversion helpers
│   │   └── main_window.py    # Legacy PyQt6 window (--legacy flag)
│   ├── core/         # Analysis algorithms (unchanged)
│   ├── models/       # Data models (unchanged)
│   ├── io/           # I/O operations
│   └── utils/        # Utilities
├── tests/            # Test suite
├── resources/        # Application resources
├── docs/             # Documentation
└── main.py          # Entry point
```

### Setting Up Development Environment

1. Clone the repository and install dependencies as shown above
2. Install development dependencies:
   ```bash
   uv sync --dev
   ```

3. Run tests:
   ```bash
   uv run pytest
   ```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_lane_detection.py

# Run napari integration tests
uv run pytest tests/test_napari_integration.py

# Run with coverage
uv run pytest --cov=gel_boy
```

### Code Style

This project follows PEP 8 guidelines. Please ensure your code is formatted properly:

```bash
# Format code
uv run black gel_boy/

# Check types
uv run mypy gel_boy/
```

## Dependencies

- **Python**: >= 3.12
- **napari**: Image viewer (replaces PyQt6 as primary GUI)
- **magicgui**: Dock-widget creation
- **NumPy**: Numerical computing
- **Pillow**: Image loading
- **matplotlib**: Profile plotting
- **scikit-image**: Image analysis utilities
- **scipy**: Peak detection and integration

See `pyproject.toml` for the complete dependency list.

> **Legacy mode**: To use the old PyQt6 interface, install the `legacy` extra
> (`pip install -e ".[legacy]"`) and run `python main.py --legacy`.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- Code follows PEP 8 style guidelines
- Tests are added for new features
- Documentation is updated as needed

## Documentation

- [User Guide](docs/user_guide.md) - How to use Gel_Boy
- [API Reference](docs/api_reference.md) - Developer API documentation
- [Napari Migration Guide](docs/NAPARI_MIGRATION.md) - v0.1 → v0.2 migration notes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- Gel_Boy Development Team

## Acknowledgments

- Built with [napari](https://napari.org)
- Inspired by the needs of gel electrophoresis researchers
- Thanks to all contributors

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the [User Guide](docs/user_guide.md)
- Review the [API Reference](docs/api_reference.md)

## Roadmap

### Version 0.1.0
- ✅ Basic project structure
- ✅ Core data models
- ✅ Skeleton GUI framework

### Version 0.2.0 (Current)
- ✅ napari-based image viewer (fixes coordinate bugs)
- ✅ Lane detection + interactive lane drawing
- ✅ Intensity profile visualization
- ✅ Peak integration with scipy
- ✅ Image operations (rotate, flip, invert)

### Version 0.3.0 (Planned)
- [ ] Band detection algorithms
- [ ] Molecular weight calibration
- [ ] Data export functionality

### Version 1.0.0 (Future)
- [ ] Complete feature set
- [ ] Comprehensive testing
- [ ] Full documentation
- [ ] Packaging for distribution