Usage
=====

Command Line Interface
---------------------

The basic syntax for i3ctl commands is:

.. code-block:: console

   $ i3ctl [options] command [subcommand] [arguments]

Global Options
-------------

- ``--verbose``, ``-v``: Increase output verbosity (can be stacked: -vv for debug level)
- ``--quiet``, ``-q``: Suppress normal output
- ``--log-file``: Specify log file path
- ``--version``: Show version and exit
- ``--help``, ``-h``: Show help message

Commands
--------

Brightness Control
~~~~~~~~~~~~~~~~~

Control screen brightness:

.. code-block:: console

   $ i3ctl brightness set 50       # Set brightness to 50%
   $ i3ctl brightness up 10        # Increase by 10%
   $ i3ctl brightness down 5       # Decrease by 5%
   $ i3ctl brightness get          # Show current brightness

Volume Control
~~~~~~~~~~~~~

Control audio volume:

.. code-block:: console

   $ i3ctl volume set 80           # Set volume to 80%
   $ i3ctl volume up 5             # Increase by 5%
   $ i3ctl volume down 10          # Decrease by 10%
   $ i3ctl volume get              # Show current volume
   $ i3ctl volume mute             # Toggle mute
   $ i3ctl volume mute --state=on  # Mute
   $ i3ctl volume mute --state=off # Unmute

Wallpaper Management
~~~~~~~~~~~~~~~~~~

Manage desktop wallpaper:

.. code-block:: console

   $ i3ctl wallpaper /path/to/image.jpg    # Set wallpaper
   $ i3ctl wallpaper --restore             # Restore last wallpaper
   $ i3ctl wallpaper --random ~/Pictures   # Random wallpaper from directory
   $ i3ctl wallpaper --list                # List wallpaper history
   $ i3ctl wallpaper --mode scale image.jpg # Set with specific scaling mode

Keyboard Layout
~~~~~~~~~~~~~

Manage keyboard layouts:

.. code-block:: console

   $ i3ctl layout switch us                # Switch to US layout
   $ i3ctl layout switch de --variant dvorak  # German Dvorak layout
   $ i3ctl layout list                     # List available layouts
   $ i3ctl layout current                  # Show current layout
   $ i3ctl layout save myLayout            # Save current layout
   $ i3ctl layout load myLayout            # Load saved layout
   $ i3ctl layout toggle us fr             # Toggle between US and French

i3 Config Management
~~~~~~~~~~~~~~~~~

Manage i3 configuration:

.. code-block:: console

   $ i3ctl config edit                     # Edit i3 config
   $ i3ctl config reload                   # Reload i3 config
   $ i3ctl config path                     # Show i3 config path
   $ i3ctl config show                     # Show i3 config

Startup Applications
~~~~~~~~~~~~~~~~~

Manage autostart applications:

.. code-block:: console

   $ i3ctl startup list                    # List startup commands
   $ i3ctl startup add "firefox"           # Add a startup command
   $ i3ctl startup add --once "nm-applet"  # Add startup command (exec)
   $ i3ctl startup remove "firefox"        # Remove a startup command

Power Management
~~~~~~~~~~~~~

Control system power state:

.. code-block:: console

   $ i3ctl power off                       # Shutdown with confirmation
   $ i3ctl power off --now                 # Immediate shutdown
   $ i3ctl power reboot                    # Reboot with confirmation
   $ i3ctl power suspend                   # Suspend system
   $ i3ctl power lock                      # Lock screen
   $ i3ctl power status                    # Show power/battery status

Network Management
~~~~~~~~~~~~~~~

Manage network connections:

.. code-block:: console

   $ i3ctl network list                    # List available networks
   $ i3ctl network list --saved            # List saved networks
   $ i3ctl network connect MyNetwork       # Connect to saved network
   $ i3ctl network connect MyNetwork --password secret  # Connect with password
   $ i3ctl network disconnect              # Disconnect from network
   $ i3ctl network status                  # Show network status
   $ i3ctl network wifi on                 # Turn WiFi on
   $ i3ctl network wifi off                # Turn WiFi off