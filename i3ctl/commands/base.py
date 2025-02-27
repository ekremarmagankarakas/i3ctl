"""
Base command class for i3ctl commands.
"""

import argparse
from abc import ABC, abstractmethod
from typing import List, Optional

from i3ctl.utils.logger import logger


class BaseCommand(ABC):
    """
    Base class for all i3ctl commands.
    """

    name = "base"
    help = "Base command"

    def __init__(self) -> None:
        """
        Initialize command.
        """
        self.parser = None

    def setup_parser(self, subparsers) -> None:
        """
        Set up command parser.

        Args:
            subparsers: Subparsers object to add command to
        """
        self.parser = subparsers.add_parser(self.name, help=self.help)
        self.parser.set_defaults(func=self.handle)
        self._setup_arguments(self.parser)

    @abstractmethod
    def _setup_arguments(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Setup command arguments. Must be implemented by subclasses.
        
        Args:
            parser: ArgumentParser to configure
            
        Returns:
            Configured ArgumentParser
        """
        pass

    @abstractmethod
    def handle(self, args: argparse.Namespace) -> int:
        """
        Handle command execution. Must be implemented by subclasses.

        Args:
            args: Command arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        pass