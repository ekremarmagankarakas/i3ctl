# Contributing to i3ctl

Thank you for considering contributing to i3ctl! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b new-feature`
3. Make your changes and add tests if possible
4. Run the existing tests to ensure nothing is broken
5. Commit your changes: `git commit -m 'Add new feature'`
6. Push to the branch: `git push origin new-feature`
7. Submit a pull request

## Development Environment

Setting up a development environment:

```bash
# Clone your fork
git clone https://github.com/yourusername/i3ctl.git
cd i3ctl

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

## Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings in Google format for all functions and classes
- Write tests for new functionality
- Update the README when adding new features

## Testing

Run tests with pytest:

```bash
pytest
```

## Pull Request Process

1. Update the README.md with details of changes to the interface, if applicable
2. Update any examples or documentation
3. The PR should work for Python 3.6 and later
4. Your PR needs to be approved by a maintainer before it can be merged

## Questions?

If you have any questions, feel free to open an issue or reach out to the maintainers.