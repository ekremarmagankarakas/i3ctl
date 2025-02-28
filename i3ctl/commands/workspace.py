"""
Workspace management commands for i3.
"""

import argparse
import json
import os
import re
import subprocess
from typing import Dict, List, Optional, Tuple, Any

from i3ctl.commands.base import BaseCommand
from i3ctl.commands import register_command
from i3ctl.commands.i3_wrapper import I3Wrapper, i3ipc_connection
from i3ctl.utils.logger import logger
from i3ctl.utils.system import run_command, check_command_exists
from i3ctl.utils.config import load_config, save_config


@register_command
class WorkspaceCommand(BaseCommand):
    """
    Command for managing i3 workspaces.
    """

    name = "workspace"
    help = "Manage i3 workspaces"

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
        
        # List workspaces
        list_parser = subparsers.add_parser("list", help="List all workspaces")
        
        # Create workspace
        create_parser = subparsers.add_parser("create", help="Create a new workspace")
        create_parser.add_argument("name", help="Name of the workspace to create")
        
        # Rename workspace
        rename_parser = subparsers.add_parser("rename", help="Rename current or specified workspace")
        rename_parser.add_argument("new_name", help="New name for the workspace")
        rename_parser.add_argument(
            "--number", "-n", 
            help="Number of the workspace to rename (current if not specified)"
        )
        
        # Go to workspace
        goto_parser = subparsers.add_parser("goto", help="Go to a workspace")
        goto_parser.add_argument("name", help="Name or number of the workspace to go to")
        
        # Move container to workspace
        move_parser = subparsers.add_parser("move", help="Move current container to a workspace")
        move_parser.add_argument("target", help="Target workspace name or number")
        
        # Show workspace on specific output
        output_parser = subparsers.add_parser("output", help="Move workspace to a specific output")
        output_parser.add_argument("workspace", help="Workspace name or number")
        output_parser.add_argument("output", help="Output name (e.g., HDMI-1, DP-1)")
        
        # Assign application to workspace
        assign_parser = subparsers.add_parser("assign", help="Assign application to workspace")
        assign_parser.add_argument("criteria", help="Window criteria (e.g., 'class=Firefox')")
        assign_parser.add_argument("workspace", help="Target workspace name or number")
        assign_parser.add_argument(
            "--add", "-a",
            action="store_true",
            help="Add to i3 config (otherwise it's temporary for this session)"
        )
        
        # Save workspace layout
        save_parser = subparsers.add_parser("save", help="Save current workspace layout")
        save_parser.add_argument(
            "name",
            help="Name to save this layout as"
        )
        save_parser.add_argument(
            "--workspace", "-w",
            help="Workspace to save (current if not specified)"
        )
        
        # Load workspace layout
        load_parser = subparsers.add_parser("load", help="Load a saved workspace layout")
        load_parser.add_argument("name", help="Name of the saved layout")
        load_parser.add_argument(
            "--workspace", "-w",
            help="Target workspace (current if not specified)"
        )
        
        # List saved layouts
        layouts_parser = subparsers.add_parser("layouts", help="List saved workspace layouts")
        
        # Delete saved layout
        delete_parser = subparsers.add_parser("delete", help="Delete a saved workspace layout")
        delete_parser.add_argument("name", help="Name of the layout to delete")
        
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
                return self._list_workspaces()
            elif args.subcommand == "create":
                return self._create_workspace(args.name)
            elif args.subcommand == "rename":
                return self._rename_workspace(args.new_name, args.number)
            elif args.subcommand == "goto":
                return self._goto_workspace(args.name)
            elif args.subcommand == "move":
                return self._move_to_workspace(args.target)
            elif args.subcommand == "output":
                return self._workspace_to_output(args.workspace, args.output)
            elif args.subcommand == "assign":
                return self._assign_to_workspace(args.criteria, args.workspace, args.add)
            elif args.subcommand == "save":
                return self._save_layout(args.name, args.workspace)
            elif args.subcommand == "load":
                return self._load_layout(args.name, args.workspace)
            elif args.subcommand == "layouts":
                return self._list_layouts()
            elif args.subcommand == "delete":
                return self._delete_layout(args.name)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error executing workspace command: {e}")
            print(f"Error: {str(e)}")
            return 1
    
    def _list_workspaces(self) -> int:
        """
        List all workspaces.
        
        Returns:
            Exit code
        """
        logger.info("Listing workspaces")
        
        try:
            workspaces = I3Wrapper.get_workspaces()
            
            if not workspaces:
                print("No workspaces found.")
                return 0
            
            print("Current workspaces:")
            for workspace in workspaces:
                focused = workspace.get("focused", False)
                visible = workspace.get("visible", False)
                urgent = workspace.get("urgent", False)
                name = workspace.get("name", "Unknown")
                output = workspace.get("output", "Unknown")
                
                status = []
                if focused:
                    status.append("focused")
                if visible:
                    status.append("visible")
                if urgent:
                    status.append("urgent")
                
                status_str = f" ({', '.join(status)})" if status else ""
                
                print(f"Workspace {name}{status_str} on output {output}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to list workspaces: {e}")
            print(f"Error: Failed to list workspaces: {e}")
            return 1
    
    def _create_workspace(self, name: str) -> int:
        """
        Create a new workspace.
        
        Args:
            name: Name of the workspace to create
            
        Returns:
            Exit code
        """
        logger.info(f"Creating workspace: {name}")
        
        # If name is just a number, convert it to a string
        if name.isdigit():
            command = ["workspace", f"number {name}"]
        else:
            command = ["workspace", name]
        
        success, result = I3Wrapper.i3_command(command)
        
        if not success:
            logger.error(f"Failed to create workspace: {name}")
            print(f"Error: Failed to create workspace: {name}")
            return 1
        
        print(f"Created and switched to workspace: {name}")
        return 0
    
    def _rename_workspace(self, new_name: str, workspace_num: Optional[str] = None) -> int:
        """
        Rename a workspace.
        
        Args:
            new_name: New name for the workspace
            workspace_num: Workspace number/name to rename (current if None)
            
        Returns:
            Exit code
        """
        logger.info(f"Renaming workspace to: {new_name}")
        
        try:
            # Get current workspace if number not provided
            old_name = workspace_num
            
            if not old_name:
                # Use i3ipc to get focused workspace name
                with i3ipc_connection() as i3:
                    focused = i3.get_tree().find_focused()
                    if focused:
                        workspace = focused.workspace()
                        if workspace:
                            old_name = workspace.name
            
            if not old_name:
                logger.error("Failed to get current workspace name")
                print("Error: Failed to get current workspace name")
                return 1
            
            # Rename workspace
            command = ["rename", "workspace", old_name, "to", new_name]
            success, result = I3Wrapper.i3_command(command)
            
            if not success:
                logger.error(f"Failed to rename workspace: {old_name} to {new_name}")
                print(f"Error: Failed to rename workspace: {old_name} to {new_name}")
                return 1
            
            print(f"Renamed workspace: {old_name} → {new_name}")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to rename workspace: {e}")
            print(f"Error: Failed to rename workspace: {e}")
            return 1
    
    def _goto_workspace(self, name: str) -> int:
        """
        Go to a workspace.
        
        Args:
            name: Name or number of the workspace
            
        Returns:
            Exit code
        """
        logger.info(f"Going to workspace: {name}")
        
        # If name is just a number, convert it to a string
        if name.isdigit():
            command = ["workspace", f"number {name}"]
        else:
            command = ["workspace", name]
        
        success, result = I3Wrapper.i3_command(command)
        
        if not success:
            logger.error(f"Failed to go to workspace: {name}")
            print(f"Error: Failed to go to workspace: {name}")
            return 1
        
        print(f"Switched to workspace: {name}")
        return 0
    
    def _move_to_workspace(self, target: str) -> int:
        """
        Move current container to a workspace.
        
        Args:
            target: Target workspace name or number
            
        Returns:
            Exit code
        """
        logger.info(f"Moving container to workspace: {target}")
        
        # If target is just a number, convert it to a string
        if target.isdigit():
            command = ["move", "container", "to", "workspace", f"number {target}"]
        else:
            command = ["move", "container", "to", "workspace", target]
        
        success, result = I3Wrapper.i3_command(command)
        
        if not success:
            logger.error(f"Failed to move container to workspace: {target}")
            print(f"Error: Failed to move container to workspace: {target}")
            return 1
        
        print(f"Moved container to workspace: {target}")
        return 0
    
    def _workspace_to_output(self, workspace: str, output: str) -> int:
        """
        Move workspace to a specific output.
        
        Args:
            workspace: Workspace name or number
            output: Output name (e.g., HDMI-1, DP-1)
            
        Returns:
            Exit code
        """
        logger.info(f"Moving workspace {workspace} to output {output}")
        
        # If workspace is just a number, convert it to a string
        if workspace.isdigit():
            command = ["workspace", f"number {workspace}", "output", output]
        else:
            command = ["workspace", workspace, "output", output]
        
        success, result = I3Wrapper.i3_command(command)
        
        if not success:
            logger.error(f"Failed to move workspace {workspace} to output {output}")
            print(f"Error: Failed to move workspace {workspace} to output {output}")
            return 1
        
        print(f"Moved workspace {workspace} to output {output}")
        return 0
    
    def _assign_to_workspace(self, criteria: str, workspace: str, add_to_config: bool = False) -> int:
        """
        Assign application to workspace.
        
        Args:
            criteria: Window criteria (e.g., 'class=Firefox')
            workspace: Target workspace name or number
            add_to_config: Whether to add to i3 config
            
        Returns:
            Exit code
        """
        logger.info(f"Assigning {criteria} to workspace {workspace}")
        
        if add_to_config:
            # Add to i3 config
            i3_config_path = self._find_i3_config()
            
            if not i3_config_path:
                logger.error("i3 config not found")
                print("Error: i3 config not found.")
                return 1
            
            try:
                # Read i3 config
                with open(i3_config_path, "r") as f:
                    content = f.readlines()
                
                # Format assign line
                if workspace.isdigit():
                    assign_line = f"assign [{criteria}] → number {workspace}\n"
                else:
                    assign_line = f"assign [{criteria}] → {workspace}\n"
                
                # Look for last assign line or insert at end
                assign_index = -1
                for i, line in enumerate(content):
                    if line.strip().startswith("assign "):
                        assign_index = i
                
                if assign_index >= 0:
                    # Insert after last assign line
                    content.insert(assign_index + 1, assign_line)
                else:
                    # Insert at end
                    content.append("\n# Window assignments\n")
                    content.append(assign_line)
                
                # Write back to config
                with open(i3_config_path, "w") as f:
                    f.writelines(content)
                
                print(f"Added assignment to i3 config: {criteria} → {workspace}")
                print("Reload i3 config to apply changes.")
                
            except Exception as e:
                logger.error(f"Failed to update i3 config: {e}")
                print(f"Error: Failed to update i3 config: {e}")
                return 1
        else:
            # Apply for current session only
            if workspace.isdigit():
                command = ["assign", f"[{criteria}]", f"workspace number {workspace}"]
            else:
                command = ["assign", f"[{criteria}]", f"workspace {workspace}"]
            
            success, result = I3Wrapper.i3_command(command)
            
            if not success:
                logger.error(f"Failed to assign {criteria} to workspace {workspace}")
                print(f"Error: Failed to assign {criteria} to workspace {workspace}")
                return 1
            
            print(f"Assigned {criteria} to workspace {workspace} (for current session only)")
        
        return 0
    
    def _save_layout(self, name: str, workspace_num: Optional[str] = None) -> int:
        """
        Save workspace layout.
        
        Args:
            name: Name to save layout as
            workspace_num: Workspace to save (current if None)
            
        Returns:
            Exit code
        """
        logger.info(f"Saving workspace layout as {name}")
        
        # Check if i3-save-tree is available
        if not check_command_exists("i3-save-tree"):
            logger.error("i3-save-tree command not found")
            print("Error: i3-save-tree command not found.")
            print("Please install i3-save-tree to use this feature.")
            return 1
        
        try:
            # Get current workspace if number not provided
            if not workspace_num:
                # Use i3ipc to get focused workspace name
                with i3ipc_connection() as i3:
                    focused = i3.get_tree().find_focused()
                    if focused:
                        workspace = focused.workspace()
                        if workspace:
                            workspace_num = workspace.name
            
            if not workspace_num:
                logger.error("Failed to get current workspace name")
                print("Error: Failed to get current workspace name")
                return 1
            
            # Create directories
            layouts_dir = os.path.expanduser("~/.config/i3ctl/layouts")
            os.makedirs(layouts_dir, exist_ok=True)
            
            # Save layout
            layout_path = os.path.join(layouts_dir, f"{name}.json")
            
            # Run i3-save-tree to get layout
            cmd = ["i3-save-tree", f"--workspace={workspace_num}"]
            return_code, stdout, stderr = run_command(cmd)
            
            if return_code != 0 or not stdout:
                logger.error(f"Failed to save workspace layout: {stderr}")
                print(f"Error: Failed to save workspace layout: {stderr}")
                return 1
            
            # Process the layout (remove comments and fix JSON)
            layout_json = ""
            for line in stdout.splitlines():
                if not line.strip().startswith("//"):
                    layout_json += line + "\n"
            
            # Save to file
            with open(layout_path, "w") as f:
                f.write(layout_json)
            
            # Update workspace layout registry in config
            config = load_config()
            if "workspace_layouts" not in config:
                config["workspace_layouts"] = {}
            
            config["workspace_layouts"][name] = {
                "path": layout_path,
                "workspace": workspace_num
            }
            
            save_config(config)
            
            print(f"Saved workspace {workspace_num} layout as '{name}'")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to save workspace layout: {e}")
            print(f"Error: Failed to save workspace layout: {e}")
            return 1
    
    def _load_layout(self, name: str, workspace_num: Optional[str] = None) -> int:
        """
        Load workspace layout.
        
        Args:
            name: Name of saved layout
            workspace_num: Target workspace (current if None)
            
        Returns:
            Exit code
        """
        logger.info(f"Loading workspace layout {name}")
        
        try:
            # Load layout registry
            config = load_config()
            layouts = config.get("workspace_layouts", {})
            
            if name not in layouts:
                logger.error(f"Layout '{name}' not found")
                print(f"Error: Layout '{name}' not found")
                return 1
            
            layout_path = layouts[name].get("path")
            
            if not layout_path or not os.path.exists(layout_path):
                logger.error(f"Layout file not found: {layout_path}")
                print(f"Error: Layout file not found: {layout_path}")
                return 1
            
            # Get current workspace if not provided
            if not workspace_num:
                # Use i3ipc to get focused workspace name
                with i3ipc_connection() as i3:
                    focused = i3.get_tree().find_focused()
                    if focused:
                        workspace = focused.workspace()
                        if workspace:
                            workspace_num = workspace.name
            
            if not workspace_num:
                logger.error("Failed to get current workspace name")
                print("Error: Failed to get current workspace name")
                return 1
            
            # Open and read layout file
            with open(layout_path, "r") as f:
                layout_content = f.read()
            
            # Create a temporary file to store the layout
            temp_path = "/tmp/i3ctl_layout.json"
            with open(temp_path, "w") as f:
                f.write(layout_content)
            
            # Append layout (this requires a running program for each placeholder in the layout)
            cmd = ["i3-msg", "append_layout", temp_path]
            return_code, stdout, stderr = run_command(cmd)
            
            if return_code != 0:
                logger.error(f"Failed to load layout: {stderr}")
                print(f"Error: Failed to load layout: {stderr}")
                return 1
            
            print(f"Loaded layout '{name}' to workspace {workspace_num}")
            print("Note: You may need to start the applications specified in the layout.")
            print("Any '[placeholder]' entries in the layout need to be filled manually.")
            
            # Clean up temporary file
            try:
                os.remove(temp_path)
            except:
                pass
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to load workspace layout: {e}")
            print(f"Error: Failed to load workspace layout: {e}")
            return 1
    
    def _list_layouts(self) -> int:
        """
        List saved workspace layouts.
        
        Returns:
            Exit code
        """
        logger.info("Listing saved workspace layouts")
        
        # Load layout registry
        config = load_config()
        layouts = config.get("workspace_layouts", {})
        
        if not layouts:
            print("No saved workspace layouts found.")
            return 0
        
        print("Saved workspace layouts:")
        for name, layout_info in layouts.items():
            workspace = layout_info.get("workspace", "Unknown")
            path = layout_info.get("path", "Unknown")
            exists = "✓" if os.path.exists(path) else "✗"
            
            print(f"- {name}: Workspace {workspace} [{exists}]")
        
        return 0
    
    def _delete_layout(self, name: str) -> int:
        """
        Delete a saved workspace layout.
        
        Args:
            name: Name of layout to delete
            
        Returns:
            Exit code
        """
        logger.info(f"Deleting workspace layout {name}")
        
        # Load layout registry
        config = load_config()
        layouts = config.get("workspace_layouts", {})
        
        if name not in layouts:
            logger.error(f"Layout '{name}' not found")
            print(f"Error: Layout '{name}' not found")
            return 1
        
        layout_path = layouts[name].get("path")
        
        # Try to delete the layout file
        if layout_path and os.path.exists(layout_path):
            try:
                os.remove(layout_path)
            except Exception as e:
                logger.warning(f"Failed to delete layout file: {e}")
                print(f"Warning: Failed to delete layout file: {e}")
        
        # Remove from registry
        del layouts[name]
        config["workspace_layouts"] = layouts
        save_config(config)
        
        print(f"Deleted workspace layout '{name}'")
        return 0
    
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