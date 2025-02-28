# i3ctl

A comprehensive command-line utility for managing i3 window manager settings.

## Features

- **Brightness Control**: Adjust screen brightness levels
- **Volume Control**: Manage audio output levels and muting
- **Wallpaper Management**: Set, rotate, and manage desktop backgrounds
- **Keyboard Layout Management**: Change and toggle between keyboard layouts
- **i3 Config Management**: Edit, reload, and manage i3 configuration
- **Startup Application Management**: Control autostart applications in i3
- **Power Management**: Handle system power states and profiles
- **Network Management**: Connect to and manage WiFi networks
- **Bluetooth Management**: Connect to and manage Bluetooth devices
- **Bar Management**: Control i3 bar visibility and i3status configuration
- **Workspace Management**: Create, rename, and manage workspaces and layouts
- **Keybinding Management**: View, add, and modify keyboard shortcuts

## Requirements

- Python 3.6 or later
- Linux system running i3 window manager
- pip package manager

### System Dependencies

Depending on which features you use, you may need some of these system tools:

- **i3-msg**: Required for i3 control (core functionality)
- **xbacklight** or **brightnessctl** or **light**: For brightness control
- **pactl** (PulseAudio) or **amixer** (ALSA): For volume control
- **feh** or **nitrogen**: For wallpaper management
- **setxkbmap**: For keyboard layout control
- **systemctl**, **powerprofilesctl**, or **tlp**: For power management
- **nmcli** (NetworkManager) or **iwctl** (iwd): For network management
- **bluetoothctl** (bluez) or **blueman-manager**: For bluetooth management

i3ctl will automatically detect which tools are available on your system and use the appropriate ones.

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

### Supported Systems

i3ctl is designed to work with:

- i3 window manager
- i3-gaps
- sway (with some limitations)

## Usage

```
i3ctl [OPTIONS] COMMAND [SUBCOMMAND] [ARGS]
```

### Global Options

- `--verbose, -v`: Increase verbosity (can be used multiple times for more detail)
- `--quiet, -q`: Suppress output
- `--log-file FILE`: Specify log file path
- `--version`: Show version and exit
- `--help, -h`: Show help message and exit

### Command Structure

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
│    ├── cancel
│    └── profile [mode]       # Set power profile (performance|balanced|power-saver|auto)
├── network
│    ├── list [--rescan] [--saved]
│    ├── connect <ssid> [--password <password>]
│    ├── disconnect
│    ├── status
│    ├── wifi {on,off}
│    └── rescan
├── bluetooth
│    ├── list [--scan] [--paired]
│    ├── connect <device>
│    ├── disconnect <device>
│    ├── pair <device>
│    ├── remove <device>
│    ├── status
│    ├── power {on,off}
│    └── scan [--timeout <seconds>] [--continuous]
├── bar
│    ├── show
│    ├── hide
│    ├── toggle
│    ├── mode {dock,hide,invisible}
│    ├── status
│    ├── config
│    │    ├── edit [--editor <editor>]
│    │    └── list
│    └── i3status
│         ├── reload
│         └── edit [--editor <editor>]
├── workspace
│    ├── list
│    ├── create <name>
│    ├── rename <new_name> [--number <workspace>]
│    ├── goto <name>
│    ├── move <target>
│    ├── output <workspace> <output>
│    ├── assign <criteria> <workspace> [--add]
│    ├── save <name> [--workspace <workspace>]
│    ├── load <name> [--workspace <workspace>]
│    ├── layouts
│    └── delete <name>
└── keybind
     ├── list [--filter <keyword>] [--mod]
     ├── add <keys> <command>
     ├── remove <keys>
     ├── show <keys>
     ├── save <name>
     ├── load <name>
     ├── profiles
     ├── delete <name>
     └── conflicts
```

## Command Details

### Brightness Control

Control screen brightness:

```bash
i3ctl brightness set 50       # Set brightness to 50%
i3ctl brightness up 10        # Increase by 10%
i3ctl brightness down 5       # Decrease by 5% 
i3ctl brightness get          # Show current brightness
```

### Volume Control

Manage audio volume:

```bash
i3ctl volume set 80           # Set volume to 80%
i3ctl volume up 5             # Increase by 5%
i3ctl volume down 10          # Decrease by 10%
i3ctl volume get              # Show current volume
i3ctl volume mute             # Toggle mute
i3ctl volume mute --state=on  # Mute
i3ctl volume mute --state=off # Unmute
```

### Wallpaper Management

Set and manage desktop wallpaper:

```bash
i3ctl wallpaper /path/to/image.jpg    # Set wallpaper
i3ctl wallpaper --restore             # Restore last wallpaper
i3ctl wallpaper --random ~/Pictures   # Random wallpaper from directory
i3ctl wallpaper --list                # List wallpaper history
i3ctl wallpaper --mode scale image.jpg # Set with specific scaling mode
```

### Keyboard Layout

Manage keyboard layouts:

```bash
i3ctl layout switch us                # Switch to US layout
i3ctl layout switch de --variant dvorak  # German Dvorak layout
i3ctl layout list                     # List available layouts
i3ctl layout current                  # Show current layout
i3ctl layout save myLayout            # Save current layout
i3ctl layout load myLayout            # Load saved layout
i3ctl layout toggle us fr             # Toggle between US and French
```

### i3 Config Management

Manage i3 configuration:

```bash
i3ctl config edit                     # Edit i3 config
i3ctl config reload                   # Reload i3 config
i3ctl config path                     # Show i3 config path
i3ctl config show                     # Show i3 config
```

### Startup Applications

Manage autostart applications:

```bash
i3ctl startup list                    # List startup commands
i3ctl startup add "firefox"           # Add a startup command
i3ctl startup add --once "nm-applet"  # Add startup command (exec)
i3ctl startup remove "firefox"        # Remove a startup command
```

### Power Management

Control system power state:

```bash
i3ctl power off                       # Shutdown with confirmation
i3ctl power off --now                 # Immediate shutdown
i3ctl power off --time 30             # Schedule shutdown in 30 minutes
i3ctl power reboot                    # Reboot with confirmation
i3ctl power suspend                   # Suspend system
i3ctl power hibernate                 # Hibernate system
i3ctl power hybrid-sleep              # Hybrid sleep mode
i3ctl power lock                      # Lock screen
i3ctl power status                    # Show power/battery status
i3ctl power cancel                    # Cancel scheduled shutdown
i3ctl power profile                   # Show current power profile
i3ctl power profile performance       # Set high-performance mode
i3ctl power profile power-saver       # Set battery-saving mode
i3ctl power profile balanced          # Set balanced mode
```

### Network Management

Manage network connections:

```bash
i3ctl network list                    # List available networks
i3ctl network list --saved            # List saved networks
i3ctl network connect MyNetwork       # Connect to saved network
i3ctl network connect MyNetwork --password secret  # Connect with password
i3ctl network disconnect              # Disconnect from network
i3ctl network status                  # Show network status
i3ctl network wifi on                 # Turn WiFi on
i3ctl network wifi off                # Turn WiFi off
i3ctl network rescan                  # Rescan for networks
```

### Bluetooth Management

Manage bluetooth devices:

```bash
i3ctl bluetooth list                  # List available bluetooth devices
i3ctl bluetooth list --paired         # List paired devices only
i3ctl bluetooth connect 00:11:22:33:44:55   # Connect to device by MAC address
i3ctl bluetooth connect "My Speaker"  # Connect to device by name
i3ctl bluetooth disconnect 00:11:22:33:44:55  # Disconnect from device
i3ctl bluetooth pair 00:11:22:33:44:55      # Pair with a device
i3ctl bluetooth remove 00:11:22:33:44:55    # Remove a paired device
i3ctl bluetooth status                # Show bluetooth status
i3ctl bluetooth power on              # Turn bluetooth on
i3ctl bluetooth power off             # Turn bluetooth off
i3ctl bluetooth scan                  # Scan for bluetooth devices
i3ctl bluetooth scan --timeout 30     # Scan for 30 seconds
i3ctl bluetooth scan --continuous     # Scan until interrupted
```

### Bar Management

Control i3 bar and i3status:

```bash
i3ctl bar show                        # Show the i3 bar
i3ctl bar hide                        # Hide the i3 bar (press Mod key to show)
i3ctl bar toggle                      # Toggle bar visibility
i3ctl bar mode dock                   # Set bar to always visible
i3ctl bar mode hide                   # Set bar to hide mode (shows on Mod key)
i3ctl bar mode invisible              # Set bar to never show
i3ctl bar status                      # Show bar status
i3ctl bar config edit                 # Edit bar configuration in i3 config
i3ctl bar config list                 # List bar configurations
i3ctl bar i3status reload             # Reload i3status configuration
i3ctl bar i3status edit               # Edit i3status configuration
```

### Workspace Management

Manage i3 workspaces and layouts:

```bash
i3ctl workspace list                  # List all workspaces
i3ctl workspace create "3: Mail"      # Create a new workspace
i3ctl workspace rename "3: Browser"   # Rename current workspace
i3ctl workspace rename "4: Chat" --number 3  # Rename workspace 3
i3ctl workspace goto 5                # Go to workspace 5
i3ctl workspace move 2                # Move container to workspace 2
i3ctl workspace output 1 HDMI-1       # Move workspace 1 to HDMI-1 output
i3ctl workspace assign "class=Firefox" 2  # Assign Firefox to workspace 2
i3ctl workspace assign "title=Terminal" "1: Terminal" --add  # Add to config
i3ctl workspace save coding           # Save current workspace layout as "coding"
i3ctl workspace load coding           # Load the "coding" workspace layout
i3ctl workspace layouts               # List saved workspace layouts
i3ctl workspace delete coding         # Delete the "coding" workspace layout
```

### Keybinding Management

Manage i3 keyboard shortcuts:

```bash
i3ctl keybind list                    # List all keybindings
i3ctl keybind list --mod              # List keybindings using mod key
i3ctl keybind list --filter exec      # Filter by keyword "exec"
i3ctl keybind add '$mod+b' 'exec firefox'  # Add new keybinding
i3ctl keybind remove '$mod+b'         # Remove a keybinding
i3ctl keybind show '$mod+Return'      # Show details for a keybinding
i3ctl keybind save default            # Save current keybindings as profile
i3ctl keybind load default            # Load saved keybinding profile
i3ctl keybind profiles                # List saved keybinding profiles
i3ctl keybind delete default          # Delete a keybinding profile
i3ctl keybind conflicts               # Check for conflicting keybindings
```

## Examples

```bash
# Adjust display brightness
i3ctl brightness up 10
i3ctl brightness set 50

# Control audio
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
i3ctl power profile performance  # Set high-performance profile
i3ctl power profile power-saver  # Set power-saving profile

# Network management
i3ctl network list
i3ctl network connect MyWiFi --password secret

# Bluetooth management
i3ctl bluetooth status
i3ctl bluetooth scan
i3ctl bluetooth connect 00:11:22:33:44:55

# Bar and i3status management
i3ctl bar toggle
i3ctl bar i3status edit
i3ctl bar mode hide

# Workspace management
i3ctl workspace list
i3ctl workspace create "3: Code"
i3ctl workspace assign "class=Firefox" 2

# Keybinding management
i3ctl keybind list --mod
i3ctl keybind add '$mod+b' 'exec firefox'
i3ctl keybind conflicts
```

## Contributing

Contributions are welcome! To contribute to i3ctl:

1. Fork the repository
2. Create a feature branch: `git checkout -b new-feature`
3. Make your changes and add tests if possible
4. Run the existing tests to ensure nothing is broken
5. Commit your changes: `git commit -m 'Add new feature'`
6. Push to the branch: `git push origin new-feature`
7. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings in Google format for all functions and classes
- Write tests for new functionality
- Update the README when adding new features

## License

This project is licensed under the MIT License - see the LICENSE file for details.