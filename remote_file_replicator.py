# Copyright Exafunction, Inc.

"""Remote file replicator between a source and target directory."""

import posixpath
from typing import Any, Callable

from file_system import FileSystem
from file_system import FileSystemEvent

# If you're completing this task in an online assessment, you can increment this
# constant to enable more unit tests relevant to the task you are on (1-5).
TASK_NUM = 1

class ReplicatorSource:
    """Class representing the source side of a file replicator."""

    def __init__(self, fs: FileSystem, dir_path: str, rpc_handle: Callable[[Any], Any]):
        self._fs = fs
        self._dir_path = dir_path
        self._rpc_handle = rpc_handle        
        # TODO
    
    def handle_event(self, event: FileSystemEvent):
        """Handle a file system event.

        Used as the callback provided to FileSystem.watchdir().
        """
        # TODO

class ReplicatorTarget:
    """Class representing the target side of a file replicator."""

    def __init__(self, fs: FileSystem, dir_path: str):
        self._fs = fs
        self._dir_path = dir_path

    def handle_request(self, request: Any) -> Any:
        """Handle a request from the ReplicatorSource."""
        # TODO