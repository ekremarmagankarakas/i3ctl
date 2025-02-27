# i3ctl Development Guidelines

## Build & Test Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python i3ctl.py [command] [subcommand] [args]

# Run tests
pytest

# Run a single test
pytest tests/test_file.py::test_function

# Lint the code
flake8
```

## Code Style Guidelines
- **Python Version**: 3.6+
- **Formatting**: Use Black for auto-formatting
- **Imports**: Group standard library, third-party, and local imports with a blank line between groups
- **Typing**: Use type hints for function parameters and return values
- **Naming Conventions**: snake_case for functions/variables, PascalCase for classes
- **Error Handling**: Use try/except blocks with specific exceptions; log errors appropriately
- **Documentation**: Docstrings in Google style format for all public functions and classes
- **Command Structure**: Follow consistent command/subcommand pattern as shown in README