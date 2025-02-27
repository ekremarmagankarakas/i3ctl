# i3ctl

A comprehensive command-line utility for managing i3 window manager settings.

## Installation

```bash
# Clone the repository
git clone https://github.com/username/i3ctl.git
cd i3ctl

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install the package in development mode
pip install -e .
```

## Usage

```
i3ctl [OPTIONS] COMMAND [SUBCOMMAND] [ARGS]
```

### Options

- `--verbose, -v`: Increase verbosity (can be used multiple times)
- `--quiet, -q`: Suppress output
- `--log-file FILE`: Specify log file path
- `--version`: Show version and exit
- `--help, -h`: Show help message and exit

### Commands

```
i3ctl
├── brightness
│    ├── set <value>
│    ├── up [<percent>]
│    ├── down [<percent>]
│    └── get
├── volume
│    ├── set <value>
│    ├── up [<percent>]
│    ├── down [<percent>]
│    ├── get
│    └── mute [--state={on,off,toggle}]
├── wallpaper 
│    ├── <path>           # Set wallpaper from path
│    ├── --list, -l       # List saved wallpapers
│    ├── --random, -r     # Set random wallpaper from a directory
│    ├── --restore, -R    # Restore last wallpaper
│    └── --mode MODE      # Set scaling mode (fill, center, tile, scale, max)
├── layout
│    ├── switch <layout> [--variant <variant>]
│    ├── list
│    ├── current
│    ├── save <name>
│    ├── load <name>
│    ├── delete <name>
│    ├── presets
│    └── toggle [<layout1> <layout2>]
├── config
│    ├── edit [--editor <editor>]
│    ├── reload
│    ├── path
│    └── show [--lines <n>]
├── startup
│    ├── add <command> [--once] [--comment <comment>]
│    ├── remove <command>
│    └── list [--all]
├── power
│    ├── off [--now] [--time <minutes>]
│    ├── reboot [--now]
│    ├── suspend [--now]
│    ├── hibernate [--now]
│    ├── hybrid-sleep [--now]
│    ├── lock
│    ├── status
│    └── cancel
└── network
     ├── list [--rescan] [--saved]
     ├── connect <ssid> [--password <password>]
     ├── disconnect
     ├── status
     ├── wifi {on,off}
     └── rescan
```

## Examples

```bash
# Brightness control
i3ctl brightness up 10
i3ctl brightness set 50

# Volume control
i3ctl volume up 5
i3ctl volume mute

# Set wallpaper
i3ctl wallpaper /path/to/image.jpg
i3ctl wallpaper --random ~/Pictures

# Switch keyboard layout
i3ctl layout switch us
i3ctl layout toggle us de

# Manage i3 config
i3ctl config edit
i3ctl config reload

# Manage startup applications
i3ctl startup list
i3ctl startup add "compton --config ~/.config/compton.conf"

# Power management
i3ctl power suspend
i3ctl power lock

# Network management
i3ctl network list
i3ctl network connect MyWiFi --password secret
```

## Contributing

Contributions are welcome! Feel free to submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
