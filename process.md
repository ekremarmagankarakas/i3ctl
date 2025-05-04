# i3ctl Process Flow and Architecture

This document explains how the i3ctl package works, the relationships between classes, and the command flow from entry point to execution.

## Overview

i3ctl is a command-line tool for controlling the i3 window manager. It provides commands for managing various aspects of the i3 environment, including:

- Volume control
- Brightness control
- Workspace management
- Keybindings
- Network settings
- Bluetooth control
- Power management
- Wallpaper management
- Bar/Status configuration
- and more

The architecture follows a command-based pattern where each feature is implemented as a separate command class, all inheriting from a common base class.

## Entry Point

The main entry point for the CLI application is the `main()` function in `i3ctl/cli.py`. When a user runs the `i3ctl` command, execution begins here.

## Command Flow

Here's the process flow when a user executes an i3ctl command:

1. The `main()` function in `cli.py` is called
2. Configuration is loaded from `~/.config/i3ctl/config.json` via `load_config()`
3. Command line arguments are parsed using `argparse`
4. Logging is configured based on verbosity flags
5. Available system tools are detected via `detect_tools()`
6. The appropriate command handler is identified and executed via `args.func(args)`
7. The command handler returns an exit code that is passed back to the shell

## Core Components

### 1. Command Registry System

The command system uses a registry pattern:

- `BaseCommand` (`commands/base.py`) - Abstract base class for all commands
- `register_command` decorator - Registers command classes in the `_commands` dictionary
- `get_command_classes()` - Returns all available commands

Each command must implement:
- `_setup_arguments()` - To define command-specific arguments
- `handle()` - To execute the command logic

### 2. Configuration Management (`utils/config.py`)

Handles loading, saving, and accessing configuration:

- `load_config()` - Loads config from file or creates default config
- `save_config()` - Saves config to file
- `get_config_value()` - Gets a specific config value
- `get_i3_config_path()` - Gets the path to the i3 configuration file

### 3. I3 Integration (`commands/i3_wrapper.py`)

Provides a wrapper around i3 commands:

- `I3Wrapper` class - Interacts with i3 window manager using i3-msg and i3ipc
- `i3ipc_connection()` - Context manager for i3ipc connection
- Methods for reloading, restarting, and getting information from i3

### 4. Logging System (`utils/logger.py`)

Manages application logging:

- `setup_logger()` - Configures the logger
- `logger` - Global logger instance

## Command Execution Process

Taking the "volume" command as an example:

1. User runs `i3ctl volume up 5`
2. `main()` in `cli.py` loads config and parses arguments
3. `VolumeCommand` is identified from the registered commands
4. `VolumeCommand.handle()` is called with the parsed arguments
5. The handler detects the appropriate volume tool (PulseAudio/ALSA)
6. The appropriate method (`_use_pulseaudio` or `_use_alsa`) is called
7. The volume command is executed using system commands via `run_command()`
8. Results are displayed to the user

## File Relationships

```
i3ctl/
├── cli.py               # Main entry point and CLI logic
├── commands/            # Command implementations
│   ├── __init__.py      # Command registry
│   ├── base.py          # Base command class
│   ├── volume.py        # Volume command example
│   ├── i3_wrapper.py    # i3 integration
│   └── ...              # Other command modules
├── utils/               # Utility functions
│   ├── config.py        # Configuration management
│   ├── logger.py        # Logging utilities
│   └── system.py        # System interaction utilities
```

## Inter-module Dependencies

- `cli.py` depends on `commands/__init__.py` for command registration
- All commands depend on `commands/base.py` for the base class
- `utils/config.py` and `utils/logger.py` are used throughout the codebase
- Most commands depend on `utils/system.py` for executing system commands

## Program Execution Flow Example

Let's take an example of `i3ctl volume up 5`:

1. `main()` in `cli.py` is called
2. Arguments are parsed, identifying "volume" as the command and "up 5" as subcommand/args
3. `VolumeCommand.handle()` is called with the parsed arguments
4. The volume tool is determined (PulseAudio or ALSA)
5. `_use_pulseaudio()` or `_use_alsa()` is called with "up" action and "5" as value
6. The appropriate system command is executed (e.g., `pactl set-sink-volume @DEFAULT_SINK@ +5%`)
7. Output is displayed to the user