Installation
============

Requirements
-----------

* Python 3.6 or later
* pip package manager
* Linux system running i3 window manager

From GitHub
----------

To install the latest development version from GitHub:

.. code-block:: console

   $ git clone https://github.com/username/i3ctl.git
   $ cd i3ctl
   $ pip install -e .

Supported Systems
----------------

i3ctl is designed to work with:

* i3 window manager
* i3-gaps
* sway (with some limitations)

System Dependencies
------------------

Depending on which features you use, you may need some of these system tools:

* i3-msg (required for i3 control)
* xbacklight or brightnessctl (for brightness control)
* pactl or amixer (for volume control)
* feh or nitrogen (for wallpaper management)
* setxkbmap (for keyboard layout control)
* systemctl (for power management)
* nmcli or iwctl (for network management)