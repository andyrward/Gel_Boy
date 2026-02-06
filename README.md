# Gel_Boy

A cross-platform gel electrophoresis image analysis and annotation tool built with Python and PyQt6.

## Overview

Gel_Boy is a desktop application designed to help researchers analyze gel electrophoresis images with features for:

- **Lane Detection**: Automatically or manually define lanes in gel images
- **Band Detection**: Identify and quantify protein or DNA bands
- **Intensity Analysis**: Generate and analyze intensity profiles for each lane
- **Molecular Weight Calibration**: Calibrate using standard ladders for accurate MW estimation
- **Annotation**: Add labels, markers, and notes to gel images
- **Export**: Export results to CSV, Excel, and annotated images

## Features (Planned)

- ✅ Cross-platform support (Windows, macOS, Linux)
- ✅ Modern PyQt6-based user interface
- ✅ Support for common image formats (PNG, JPEG, TIFF, BMP)
- ✅ Automatic lane detection algorithms
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
pip install -r requirements.txt
python main.py
```

## Quick Start

1. **Launch Gel_Boy**: Run `uv run python main.py`
2. **Load an Image**: File → Open Image
3. **Detect Lanes**: Analysis → Auto-Detect Lanes (or manually define)
4. **Detect Bands**: Analysis → Detect Bands
5. **Export Results**: File → Export → CSV/Excel

For detailed instructions, see the [User Guide](docs/user_guide.md).

## Development

### Project Structure

```
Gel_Boy/
├── gel_boy/           # Main package
│   ├── gui/          # GUI components
│   ├── core/         # Analysis algorithms
│   ├── models/       # Data models
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
- **PyQt6**: GUI framework
- **NumPy**: Numerical computing
- **Pillow**: Image processing
- **pytest**: Testing framework

See `pyproject.toml` for complete dependency list.

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- Gel_Boy Development Team

## Acknowledgments

- Built with PyQt6
- Inspired by the needs of gel electrophoresis researchers
- Thanks to all contributors

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the [User Guide](docs/user_guide.md)
- Review the [API Reference](docs/api_reference.md)

## Roadmap

### Version 0.1.0 (Current)
- ✅ Basic project structure
- ✅ Core data models
- ✅ Skeleton GUI framework

### Version 0.2.0 (Planned)
- [ ] Image loading and display
- [ ] Basic lane detection
- [ ] Intensity profile visualization

### Version 0.3.0 (Planned)
- [ ] Band detection algorithms
- [ ] Molecular weight calibration
- [ ] Data export functionality

### Version 1.0.0 (Future)
- [ ] Complete feature set
- [ ] Comprehensive testing
- [ ] Full documentation
- [ ] Packaging for distribution