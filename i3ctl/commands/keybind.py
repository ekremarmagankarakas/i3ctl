"""
Keybinding management commands for i3.
"""

import argparse
import os
import re
import subprocess
from typing import Dict, List, Optional, Tuple, Any, Set

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.commands.i3_wrapper import I3Wrapper
from i3ctl.utils.logger import logger
from i3ctl.utils.system import run_command, check_command_exists
from i3ctl.utils.config import load_config, save_config


@register_command
class KeybindCommand(BaseCommand):
    """
    Command for managing i3 keybindings.
    """

    name = "keybind"
    help = "Manage i3 keybindings"

    def _setup_arguments(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Set up command arguments.
        
        Args:
            parser: ArgumentParser to configure
            
        Returns:
            Configured ArgumentParser
        """
        self.parser = parser  # Save the parser for later use
        subparsers = parser.add_subparsers(dest="subcommand")
        
        # List keybindings
        list_parser = subparsers.add_parser("list", help="List all keybindings")
        list_parser.add_argument(
            "--filter", "-f",
            help="Filter bindings by keyword"
        )
        list_parser.add_argument(
            "--mod", "-m",
            action="store_true",
            help="Show only bindings using the mod key"
        )
        
        # Add keybinding
        add_parser = subparsers.add_parser("add", help="Add a new keybinding")
        add_parser.add_argument("keys", help="Key combination (e.g., '$mod+Shift+a')")
        add_parser.add_argument("command", help="Command to execute")
        
        # Remove keybinding
        remove_parser = subparsers.add_parser("remove", help="Remove a keybinding")
        remove_parser.add_argument("keys", help="Key combination to remove (e.g., '$mod+Shift+a')")
        
        # Show keybinding details
        show_parser = subparsers.add_parser("show", help="Show details for a specific keybinding")
        show_parser.add_argument("keys", help="Key combination to show (e.g., '$mod+Shift+a')")
        
        # Save keybinding profile
        save_parser = subparsers.add_parser("save", help="Save current keybindings as a profile")
        save_parser.add_argument("name", help="Profile name")
        
        # Load keybinding profile
        load_parser = subparsers.add_parser("load", help="Load a saved keybinding profile")
        load_parser.add_argument("name", help="Profile name")
        
        # List saved profiles
        profiles_parser = subparsers.add_parser("profiles", help="List saved keybinding profiles")
        
        # Delete a profile
        delete_parser = subparsers.add_parser("delete", help="Delete a saved keybinding profile")
        delete_parser.add_argument("name", help="Profile name to delete")
        
        # Check for conflicts
        conflicts_parser = subparsers.add_parser("conflicts", help="Check for conflicting keybindings")
        
        return parser

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
        
        # Check if i3 is available
        try:
            I3Wrapper.ensure_i3()
        except Exception as e:
            logger.error(f"i3 not found: {e}")
            print(f"Error: i3 not found. {e}")
            return 1
        
        try:
            # Handle subcommands
            if args.subcommand == "list":
                return self._list_keybindings(args.filter, args.mod)
            elif args.subcommand == "add":
                return self._add_keybinding(args.keys, args.command)
            elif args.subcommand == "remove":
                return self._remove_keybinding(args.keys)
            elif args.subcommand == "show":
                return self._show_keybinding(args.keys)
            elif args.subcommand == "save":
                return self._save_profile(args.name)
            elif args.subcommand == "load":
                return self._load_profile(args.name)
            elif args.subcommand == "profiles":
                return self._list_profiles()
            elif args.subcommand == "delete":
                return self._delete_profile(args.name)
            elif args.subcommand == "conflicts":
                return self._check_conflicts()
            
            return 0
            
        except Exception as e:
            logger.error(f"Error executing keybind command: {e}")
            print(f"Error: {str(e)}")
            return 1
    
    def _list_keybindings(self, filter_keyword: Optional[str] = None, mod_only: bool = False) -> int:
        """
        List all keybindings.
        
        Args:
            filter_keyword: Keyword to filter bindings
            mod_only: Show only bindings using the mod key
            
        Returns:
            Exit code
        """
        logger.info("Listing keybindings")
        
        # Get i3 config
        i3_config_path = self._find_i3_config()
        
        if not i3_config_path:
            logger.error("i3 config not found")
            print("Error: i3 config not found.")
            return 1
        
        try:
            # Parse config file to extract bindings
            with open(i3_config_path, "r") as f:
                content = f.read()
            
            # Extract bindsym lines
            bindings = []
            for line in content.splitlines():
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Check for binding lines
                if line.startswith("bindsym ") or line.startswith("bindcode "):
                    parts = line.split(" ", 2)
                    if len(parts) >= 3:
                        binding_type = parts[0]  # bindsym or bindcode
                        key = parts[1]
                        command = parts[2]
                        
                        # Apply filters
                        if mod_only and "$mod" not in key:
                            continue
                            
                        if filter_keyword and filter_keyword.lower() not in line.lower():
                            continue
                        
                        bindings.append({
                            "type": binding_type,
                            "key": key,
                            "command": command
                        })
            
            if not bindings:
                if filter_keyword:
                    print(f"No keybindings found matching '{filter_keyword}'.")
                else:
                    print("No keybindings found.")
                return 0
            
            # Display bindings
            print(f"Found {len(bindings)} keybindings:")
            
            # Group by key prefix for better organization
            grouped_bindings = {}
            for binding in bindings:
                key_parts = binding["key"].split("+")
                if len(key_parts) > 1:
                    prefix = "+".join(key_parts[:-1])
                    if prefix not in grouped_bindings:
                        grouped_bindings[prefix] = []
                    grouped_bindings[prefix].append(binding)
                else:
                    # Handle single keys
                    if "Single Keys" not in grouped_bindings:
                        grouped_bindings["Single Keys"] = []
                    grouped_bindings["Single Keys"].append(binding)
            
            # Display by group
            for group, group_bindings in sorted(grouped_bindings.items()):
                print(f"\n{group}:")
                for binding in sorted(group_bindings, key=lambda x: x["key"]):
                    print(f"  {binding['key']} → {binding['command']}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to list keybindings: {e}")
            print(f"Error: Failed to list keybindings: {e}")
            return 1
    
    def _add_keybinding(self, keys: str, command: str) -> int:
        """
        Add a new keybinding.
        
        Args:
            keys: Key combination
            command: Command to execute
            
        Returns:
            Exit code
        """
        logger.info(f"Adding keybinding: {keys} → {command}")
        
        # Get i3 config
        i3_config_path = self._find_i3_config()
        
        if not i3_config_path:
            logger.error("i3 config not found")
            print("Error: i3 config not found.")
            return 1
        
        try:
            # Read config file
            with open(i3_config_path, "r") as f:
                content = f.readlines()
            
            # Check if binding already exists
            binding_line = f"bindsym {keys} {command}\n"
            for i, line in enumerate(content):
                if line.strip() == f"bindsym {keys} {command}":
                    logger.warning(f"Keybinding already exists: {keys}")
                    print(f"Keybinding already exists: {keys} → {command}")
                    return 0
            
            # Find the right place to add the binding
            # Look for the last bindsym line
            last_binding_index = -1
            for i, line in enumerate(content):
                if line.strip().startswith("bindsym "):
                    last_binding_index = i
            
            if last_binding_index >= 0:
                # Insert after last binding
                content.insert(last_binding_index + 1, binding_line)
            else:
                # If no bindings found, add to end of file
                content.append("\n# Custom keybinding\n")
                content.append(binding_line)
            
            # Write back to file
            with open(i3_config_path, "w") as f:
                f.writelines(content)
            
            print(f"Added keybinding: {keys} → {command}")
            print("Reload i3 config to apply changes.")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to add keybinding: {e}")
            print(f"Error: Failed to add keybinding: {e}")
            return 1
    
    def _remove_keybinding(self, keys: str) -> int:
        """
        Remove a keybinding.
        
        Args:
            keys: Key combination to remove
            
        Returns:
            Exit code
        """
        logger.info(f"Removing keybinding: {keys}")
        
        # Get i3 config
        i3_config_path = self._find_i3_config()
        
        if not i3_config_path:
            logger.error("i3 config not found")
            print("Error: i3 config not found.")
            return 1
        
        try:
            # Read config file
            with open(i3_config_path, "r") as f:
                content = f.readlines()
            
            # Find and remove the binding
            found = False
            new_content = []
            pattern = re.compile(rf"^\s*bindsym\s+{re.escape(keys)}\s+")
            
            for line in content:
                if pattern.match(line.strip()):
                    found = True
                    # Skip this line (don't add to new_content)
                else:
                    new_content.append(line)
            
            if not found:
                logger.warning(f"Keybinding not found: {keys}")
                print(f"Keybinding not found: {keys}")
                return 1
            
            # Write back to file
            with open(i3_config_path, "w") as f:
                f.writelines(new_content)
            
            print(f"Removed keybinding: {keys}")
            print("Reload i3 config to apply changes.")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to remove keybinding: {e}")
            print(f"Error: Failed to remove keybinding: {e}")
            return 1
    
    def _show_keybinding(self, keys: str) -> int:
        """
        Show details for a specific keybinding.
        
        Args:
            keys: Key combination to show
            
        Returns:
            Exit code
        """
        logger.info(f"Showing keybinding details: {keys}")
        
        # Get i3 config
        i3_config_path = self._find_i3_config()
        
        if not i3_config_path:
            logger.error("i3 config not found")
            print("Error: i3 config not found.")
            return 1
        
        try:
            # Read config file
            with open(i3_config_path, "r") as f:
                content = f.read()
            
            # Find the binding
            pattern = re.compile(rf"bindsym\s+{re.escape(keys)}\s+(.+)")
            matches = []
            
            for line in content.splitlines():
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                match = pattern.match(line)
                if match:
                    command = match.group(1)
                    matches.append({
                        "keys": keys,
                        "command": command,
                        "line": line
                    })
            
            if not matches:
                logger.warning(f"Keybinding not found: {keys}")
                print(f"Keybinding not found: {keys}")
                return 1
            
            # Display binding details
            print(f"Keybinding details for '{keys}':")
            for i, match in enumerate(matches, 1):
                if len(matches) > 1:
                    print(f"\nBinding #{i}:")
                
                print(f"  Command: {match['command']}")
                
                # Parse the key combination
                key_parts = keys.split("+")
                if len(key_parts) > 1:
                    print("  Modifiers:")
                    for i, part in enumerate(key_parts[:-1]):
                        print(f"    - {part}")
                    print(f"  Key: {key_parts[-1]}")
                else:
                    print(f"  Key: {keys}")
                
                # Add tips for the binding
                if "$mod" in keys:
                    print("\nNote: $mod is typically set to Super (Windows key) or Alt in your i3 config.")
                
                if "exec" in match["command"]:
                    print("  Type: Executes external command")
                elif "workspace" in match["command"]:
                    print("  Type: Workspace management")
                elif "focus" in match["command"] or "move" in match["command"]:
                    print("  Type: Window management")
                elif "mode" in match["command"]:
                    print("  Type: Mode change")
                else:
                    print("  Type: i3 internal command")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to show keybinding: {e}")
            print(f"Error: Failed to show keybinding: {e}")
            return 1
    
    def _save_profile(self, name: str) -> int:
        """
        Save current keybindings as a profile.
        
        Args:
            name: Profile name
            
        Returns:
            Exit code
        """
        logger.info(f"Saving keybinding profile: {name}")
        
        # Get i3 config
        i3_config_path = self._find_i3_config()
        
        if not i3_config_path:
            logger.error("i3 config not found")
            print("Error: i3 config not found.")
            return 1
        
        try:
            # Read config file
            with open(i3_config_path, "r") as f:
                content = f.read()
            
            # Extract all bindings
            bindings = []
            for line in content.splitlines():
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Check for binding lines
                if line.startswith("bindsym ") or line.startswith("bindcode "):
                    bindings.append(line)
            
            if not bindings:
                logger.warning("No keybindings found in config")
                print("No keybindings found in config.")
                return 1
            
            # Create directories
            keybind_dir = os.path.expanduser("~/.config/i3ctl/keybindings")
            os.makedirs(keybind_dir, exist_ok=True)
            
            # Save bindings to file
            profile_path = os.path.join(keybind_dir, f"{name}.conf")
            with open(profile_path, "w") as f:
                f.write("\n".join(bindings))
            
            # Update keybinding profile registry in config
            config = load_config()
            if "keybinding_profiles" not in config:
                config["keybinding_profiles"] = {}
            
            config["keybinding_profiles"][name] = {
                "path": profile_path,
                "count": len(bindings)
            }
            
            save_config(config)
            
            print(f"Saved {len(bindings)} keybindings as profile '{name}'")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to save keybinding profile: {e}")
            print(f"Error: Failed to save keybinding profile: {e}")
            return 1
    
    def _load_profile(self, name: str) -> int:
        """
        Load a saved keybinding profile.
        
        Args:
            name: Profile name
            
        Returns:
            Exit code
        """
        logger.info(f"Loading keybinding profile: {name}")
        
        # Load profile registry
        config = load_config()
        profiles = config.get("keybinding_profiles", {})
        
        if name not in profiles:
            logger.error(f"Profile '{name}' not found")
            print(f"Error: Profile '{name}' not found")
            return 1
        
        profile_path = profiles[name].get("path")
        
        if not profile_path or not os.path.exists(profile_path):
            logger.error(f"Profile file not found: {profile_path}")
            print(f"Error: Profile file not found: {profile_path}")
            return 1
        
        # Get i3 config
        i3_config_path = self._find_i3_config()
        
        if not i3_config_path:
            logger.error("i3 config not found")
            print("Error: i3 config not found.")
            return 1
        
        try:
            # Read profile file
            with open(profile_path, "r") as f:
                bindings = f.read().splitlines()
            
            # Read current config
            with open(i3_config_path, "r") as f:
                content = f.readlines()
            
            # Remove all existing keybindings
            new_content = []
            for line in content:
                strip_line = line.strip()
                if not (strip_line.startswith("bindsym ") or strip_line.startswith("bindcode ")):
                    new_content.append(line)
            
            # Find a good place to insert the bindings (after mode definitions)
            insert_index = len(new_content)
            for i, line in enumerate(new_content):
                if "set $mod " in line:
                    # Insert after mod key definition
                    insert_index = i + 1
                    break
            
            # Insert bindings
            new_content.insert(insert_index, "\n# Keybindings from profile: " + name + "\n")
            for binding in bindings:
                new_content.insert(insert_index + 1, binding + "\n")
                insert_index += 1
            
            # Write back to file
            with open(i3_config_path, "w") as f:
                f.writelines(new_content)
            
            print(f"Loaded {len(bindings)} keybindings from profile '{name}'")
            print("Reload i3 config to apply changes.")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to load keybinding profile: {e}")
            print(f"Error: Failed to load keybinding profile: {e}")
            return 1
    
    def _list_profiles(self) -> int:
        """
        List saved keybinding profiles.
        
        Returns:
            Exit code
        """
        logger.info("Listing keybinding profiles")
        
        # Load profile registry
        config = load_config()
        profiles = config.get("keybinding_profiles", {})
        
        if not profiles:
            print("No saved keybinding profiles found.")
            return 0
        
        print("Saved keybinding profiles:")
        for name, profile_info in profiles.items():
            count = profile_info.get("count", "?")
            path = profile_info.get("path", "Unknown")
            exists = "✓" if os.path.exists(path) else "✗"
            
            print(f"- {name}: {count} keybindings [{exists}]")
        
        return 0
    
    def _delete_profile(self, name: str) -> int:
        """
        Delete a saved keybinding profile.
        
        Args:
            name: Profile name to delete
            
        Returns:
            Exit code
        """
        logger.info(f"Deleting keybinding profile: {name}")
        
        # Load profile registry
        config = load_config()
        profiles = config.get("keybinding_profiles", {})
        
        if name not in profiles:
            logger.error(f"Profile '{name}' not found")
            print(f"Error: Profile '{name}' not found")
            return 1
        
        profile_path = profiles[name].get("path")
        
        # Try to delete the profile file
        if profile_path and os.path.exists(profile_path):
            try:
                os.remove(profile_path)
            except Exception as e:
                logger.warning(f"Failed to delete profile file: {e}")
                print(f"Warning: Failed to delete profile file: {e}")
        
        # Remove from registry
        del profiles[name]
        config["keybinding_profiles"] = profiles
        save_config(config)
        
        print(f"Deleted keybinding profile '{name}'")
        return 0
    
    def _check_conflicts(self) -> int:
        """
        Check for conflicting keybindings.
        
        Returns:
            Exit code
        """
        logger.info("Checking for keybinding conflicts")
        
        # Get i3 config
        i3_config_path = self._find_i3_config()
        
        if not i3_config_path:
            logger.error("i3 config not found")
            print("Error: i3 config not found.")
            return 1
        
        try:
            # Read config file
            with open(i3_config_path, "r") as f:
                content = f.read()
            
            # Extract all bindings
            key_map = {}
            for line_num, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Check for binding lines
                if line.startswith("bindsym "):
                    parts = line.split(" ", 2)
                    if len(parts) >= 3:
                        key = parts[1]
                        command = parts[2]
                        
                        if key in key_map:
                            key_map[key].append({
                                "line": line_num,
                                "command": command,
                                "full_line": line
                            })
                        else:
                            key_map[key] = [{
                                "line": line_num,
                                "command": command,
                                "full_line": line
                            }]
            
            # Find conflicts
            conflicts = {}
            for key, bindings in key_map.items():
                if len(bindings) > 1:
                    conflicts[key] = bindings
            
            if not conflicts:
                print("No keybinding conflicts found.")
                return 0
            
            # Display conflicts
            print(f"Found {len(conflicts)} keybinding conflicts:")
            
            for key, bindings in conflicts.items():
                print(f"\nConflict on key combination: {key}")
                for i, binding in enumerate(bindings, 1):
                    print(f"  Binding #{i} (line {binding['line']}): {binding['command']}")
            
            print("\nRecommendation: Review and resolve conflicts to avoid unpredictable behavior.")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to check keybinding conflicts: {e}")
            print(f"Error: Failed to check keybinding conflicts: {e}")
            return 1
    
    def _find_i3_config(self) -> Optional[str]:
        """
        Find i3 config file.
        
        Returns:
            Path to i3 config file or None if not found
        """
        # Common i3 config locations
        locations = [
            os.path.expanduser("~/.config/i3/config"),
            os.path.expanduser("~/.i3/config"),
            "/etc/i3/config"
        ]
        
        for location in locations:
            if os.path.isfile(location):
                return location
        
        return None