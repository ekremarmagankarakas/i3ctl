"""
Keyboard layout management commands.
"""

import argparse
import os
import re
import json
from typing import Dict, List, Optional, Tuple

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.utils.logger import logger
from i3ctl.utils.config import get_config_value, load_config, save_config
from i3ctl.utils.system import run_command, check_command_exists


@register_command
class LayoutCommand(BaseCommand):
    """
    Command for managing keyboard layouts.
    """

    name = "layout"
    help = "Manage keyboard layouts"

    def _setup_arguments(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Set up command arguments.
        
        Args:
            parser: ArgumentParser to configure
            
        Returns:
            Configured ArgumentParser
        """
        self.parser = parser  # Save the parser for later use
        subparsers = self.parser.add_subparsers(dest="subcommand")
        
        # Switch to a layout
        switch_parser = subparsers.add_parser("switch", help="Switch to a keyboard layout")
        switch_parser.add_argument("layout", help="Layout to switch to (e.g., 'us', 'de', 'fr')")
        switch_parser.add_argument("--variant", "-v", help="Layout variant (e.g., 'dvorak', 'colemak')")
        
        # List available layouts
        list_parser = subparsers.add_parser("list", help="List available keyboard layouts")
        
        # Show current layout
        current_parser = subparsers.add_parser("current", help="Show current keyboard layout")
        
        # Save layout preset
        save_parser = subparsers.add_parser("save", help="Save current layout as a preset")
        save_parser.add_argument("name", help="Name for the preset")
        
        # Load layout preset
        load_parser = subparsers.add_parser("load", help="Load a saved layout preset")
        load_parser.add_argument("name", help="Name of the preset to load")
        
        # Delete layout preset
        delete_parser = subparsers.add_parser("delete", help="Delete a saved layout preset")
        delete_parser.add_argument("name", help="Name of the preset to delete")
        
        # List saved layout presets
        presets_parser = subparsers.add_parser("presets", help="List saved layout presets")
        
        # Toggle between two layouts
        toggle_parser = subparsers.add_parser("toggle", help="Toggle between two layouts")
        toggle_parser.add_argument("layout1", nargs="?", help="First layout (e.g., 'us')")
        toggle_parser.add_argument("layout2", nargs="?", help="Second layout (e.g., 'de')")

    def handle(self, args: argparse.Namespace) -> int:
        """
        Handle command execution.

        Args:
            args: Command arguments
        
        Returns:
            Exit code
        """
        if not args.subcommand:
            self.parser.print_help()
            return 0
        
        # Check if setxkbmap is available
        if not check_command_exists("setxkbmap"):
            logger.error("setxkbmap command not found")
            print("Error: setxkbmap command not found.")
            print("Please install the xkeyboard-config package.")
            return 0
        
        # Handle subcommands
        if args.subcommand == "switch":
            self._switch_layout(args.layout, args.variant)
        elif args.subcommand == "list":
            self._list_layouts()
        elif args.subcommand == "current":
            self._show_current_layout()
        elif args.subcommand == "save":
            self._save_layout_preset(args.name)
        elif args.subcommand == "load":
            self._load_layout_preset(args.name)
        elif args.subcommand == "delete":
            self._delete_layout_preset(args.name)
        elif args.subcommand == "presets":
            self._list_layout_presets()
        elif args.subcommand == "toggle":
            self._toggle_layouts(args.layout1, args.layout2)
            
        return 0
    
    def _switch_layout(self, layout: str, variant: Optional[str] = None) -> None:
        """
        Switch to a specific keyboard layout.

        Args:
            layout: Keyboard layout code (e.g., 'us', 'de')
            variant: Optional variant (e.g., 'dvorak', 'colemak')
        """
        cmd = ["setxkbmap", layout]
        
        if variant:
            cmd.extend(["-variant", variant])
        
        logger.info(f"Switching keyboard layout to {layout}" + (f" (variant: {variant})" if variant else ""))
        print(f"Switching keyboard layout to {layout}" + (f" (variant: {variant})" if variant else ""))
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to switch layout: {stderr}")
            print(f"Error: Failed to switch layout: {stderr}")
            return
        
        # Save current layout to config
        config = load_config()
        config["current_layout"] = {"layout": layout, "variant": variant}
        save_config(config)
        
        print(f"Keyboard layout switched to {layout}" + (f" (variant: {variant})" if variant else ""))
    
    def _list_layouts(self) -> None:
        """
        List available keyboard layouts.
        """
        print("Available keyboard layouts:")
        
        # Get list of layouts from the system
        return_code, stdout, stderr = run_command(["localectl", "list-x11-keymap-layouts"])
        
        if return_code != 0 or not stdout:
            # Try alternative method
            if check_command_exists("grep") and os.path.exists("/usr/share/X11/xkb/rules/base.lst"):
                _, stdout, _ = run_command(["grep", "^! layout", "-A", "500", "/usr/share/X11/xkb/rules/base.lst"])
                
                if stdout:
                    # Parse the layout list
                    layouts = []
                    capture = False
                    for line in stdout.splitlines():
                        if line.startswith("! layout"):
                            capture = True
                            continue
                        elif line.startswith("!"):
                            capture = False
                            continue
                        
                        if capture and line.strip():
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                layout_code = parts[0]
                                layout_name = " ".join(parts[1:])
                                layouts.append(f"{layout_code}: {layout_name}")
                    
                    if layouts:
                        print("\n".join(layouts))
                        return
            
            # Fallback to a minimal list of common layouts
            print("Could not retrieve complete layout list. Here are some common layouts:")
            print("us: English (US)")
            print("de: German")
            print("fr: French")
            print("gb: English (UK)")
            print("it: Italian")
            print("es: Spanish")
            print("ru: Russian")
            print("jp: Japanese")
            print("cn: Chinese")
            print("\nFor a complete list, try running: localectl list-x11-keymap-layouts")
            return
        
        # Print the layouts
        layouts = stdout.strip().split("\n")
        for layout in layouts:
            print(f"- {layout}")
    
    def _show_current_layout(self) -> None:
        """
        Show current keyboard layout.
        """
        # First try to get from setxkbmap
        return_code, stdout, stderr = run_command(["setxkbmap", "-query"])
        
        if return_code == 0 and stdout:
            layout = None
            variant = None
            
            for line in stdout.splitlines():
                if "layout" in line:
                    parts = line.strip().split(":")
                    if len(parts) >= 2:
                        layout = parts[1].strip()
                elif "variant" in line:
                    parts = line.strip().split(":")
                    if len(parts) >= 2:
                        variant = parts[1].strip()
            
            if layout:
                print(f"Current keyboard layout: {layout}" + (f" (variant: {variant})" if variant else ""))
                return
        
        # Fallback to checking the config file
        config = load_config()
        current_layout = config.get("current_layout", {})
        
        if current_layout:
            layout = current_layout.get("layout")
            variant = current_layout.get("variant")
            
            if layout:
                print(f"Current keyboard layout: {layout}" + (f" (variant: {variant})" if variant else ""))
                return
        
        print("Could not determine current keyboard layout.")
    
    def _save_layout_preset(self, name: str) -> None:
        """
        Save current layout as a preset.

        Args:
            name: Name for the preset
        """
        # Get current layout
        return_code, stdout, stderr = run_command(["setxkbmap", "-query"])
        
        if return_code != 0 or not stdout:
            logger.error("Failed to get current layout")
            print("Error: Failed to get current layout.")
            return
        
        # Parse the output
        layout = None
        variant = None
        options = None
        
        for line in stdout.splitlines():
            if "layout" in line:
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    layout = parts[1].strip()
            elif "variant" in line:
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    variant = parts[1].strip()
            elif "options" in line:
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    options = parts[1].strip()
        
        if not layout:
            logger.error("Could not determine current layout")
            print("Error: Could not determine current layout.")
            return
        
        # Save the preset
        config = load_config()
        
        if "layout_presets" not in config:
            config["layout_presets"] = {}
        
        config["layout_presets"][name] = {
            "layout": layout,
            "variant": variant,
            "options": options
        }
        
        save_config(config)
        
        print(f"Layout preset '{name}' saved: {layout}" + (f" (variant: {variant})" if variant else ""))
    
    def _load_layout_preset(self, name: str) -> None:
        """
        Load a saved layout preset.

        Args:
            name: Name of the preset to load
        """
        config = load_config()
        presets = config.get("layout_presets", {})
        
        if name not in presets:
            logger.error(f"Layout preset not found: {name}")
            print(f"Error: Layout preset not found: {name}")
            return
        
        preset = presets[name]
        layout = preset.get("layout")
        variant = preset.get("variant")
        options = preset.get("options")
        
        if not layout:
            logger.error(f"Invalid layout preset: {name}")
            print(f"Error: Invalid layout preset: {name}")
            return
        
        # Build the command
        cmd = ["setxkbmap", layout]
        
        if variant:
            cmd.extend(["-variant", variant])
        
        if options:
            cmd.extend(["-options", options])
        
        logger.info(f"Loading layout preset '{name}': {layout}" + (f" (variant: {variant})" if variant else ""))
        print(f"Loading layout preset '{name}': {layout}" + (f" (variant: {variant})" if variant else ""))
        
        return_code, stdout, stderr = run_command(cmd)
        
        if return_code != 0:
            logger.error(f"Failed to load layout preset: {stderr}")
            print(f"Error: Failed to load layout preset: {stderr}")
            return
        
        # Save current layout to config
        config["current_layout"] = {"layout": layout, "variant": variant}
        save_config(config)
        
        print(f"Keyboard layout switched to preset '{name}'")
    
    def _delete_layout_preset(self, name: str) -> None:
        """
        Delete a saved layout preset.

        Args:
            name: Name of the preset to delete
        """
        config = load_config()
        presets = config.get("layout_presets", {})
        
        if name not in presets:
            logger.error(f"Layout preset not found: {name}")
            print(f"Error: Layout preset not found: {name}")
            return
        
        # Delete the preset
        del presets[name]
        config["layout_presets"] = presets
        save_config(config)
        
        print(f"Layout preset '{name}' deleted.")
    
    def _list_layout_presets(self) -> None:
        """
        List saved layout presets.
        """
        config = load_config()
        presets = config.get("layout_presets", {})
        
        if not presets:
            print("No layout presets found.")
            return
        
        print("Saved layout presets:")
        for name, preset in presets.items():
            layout = preset.get("layout", "unknown")
            variant = preset.get("variant")
            print(f"- {name}: {layout}" + (f" (variant: {variant})" if variant else ""))
    
    def _toggle_layouts(self, layout1: Optional[str], layout2: Optional[str]) -> None:
        """
        Toggle between two layouts.

        Args:
            layout1: First layout (e.g., 'us')
            layout2: Second layout (e.g., 'de')
        """
        # If layouts not provided, try to get from config
        if not layout1 or not layout2:
            config = load_config()
            toggle_layouts = config.get("toggle_layouts", [])
            
            if len(toggle_layouts) >= 2:
                layout1 = toggle_layouts[0]
                layout2 = toggle_layouts[1]
            else:
                # Fallback to common toggle between US and another layout
                layout1 = layout1 or "us"
                layout2 = layout2 or "de"  # Default to German as second layout
        
        # Get current layout
        return_code, stdout, stderr = run_command(["setxkbmap", "-query"])
        
        if return_code != 0 or not stdout:
            logger.error("Failed to get current layout")
            print("Error: Failed to get current layout.")
            return
        
        # Parse current layout
        current_layout = None
        for line in stdout.splitlines():
            if "layout" in line:
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    current_layout = parts[1].strip()
                    break
        
        if not current_layout:
            logger.error("Could not determine current layout")
            print("Error: Could not determine current layout.")
            return
        
        # Determine which layout to switch to
        new_layout = layout2 if current_layout == layout1 else layout1
        
        # Switch to the new layout
        logger.info(f"Toggling layout from {current_layout} to {new_layout}")
        print(f"Toggling layout from {current_layout} to {new_layout}")
        
        return_code, stdout, stderr = run_command(["setxkbmap", new_layout])
        
        if return_code != 0:
            logger.error(f"Failed to toggle layout: {stderr}")
            print(f"Error: Failed to toggle layout: {stderr}")
            return
        
        # Save current layout to config
        config = load_config()
        config["current_layout"] = {"layout": new_layout, "variant": None}
        
        # Save toggle layouts
        config["toggle_layouts"] = [layout1, layout2]
        save_config(config)
        
        print(f"Keyboard layout toggled to {new_layout}")