# Copyright Exafunction, Inc.

"""Remote file replicator between a source and target directory."""

"""
Question (rough notes, not exact text):

# Requirements
- Replicator for directories (one machine to another)
- When any changes occur on the source machine, sync to target machine
- "replicator*s*" - multiple replicators?
- While they are copying, nothing else will be modifying -> No locking required?

## Replicators
- ReplicatorSource and ReplicatorTarget
- Both access their respective directory.
- Communicate with RPC (Source calls functions on Target)

## Specifics
- ReplicatorSource can call its `self._rpc_handle` function
  which corresponds to calling `handle_request` on the Target.
- MUST DEFINE REQUEST AND RESPONSE TYPES <<<<<<
- Both must be pickleable py objects (python stdlib stuff is usually pickleable)

## Filesystem API
- `file_system.py`
- posixpath.join, posixpath.basename, dirname, relpath
  (posixpath is like os.path but works on Windows) - dont use os.path! Mock FS

- ReplicatorSource can also ask the filesystem to WATCH for changes
  using a callback whenever FS has events.
  `self._fs.watchdir(dir_path, self.handle_event)
- Watching a dir consumes valuable system resource, so remove them if they are
  no longer needed: `self._fs.unwatchdir(dir_path)`

For each dir, three kinds of file system events:
- file or subdir added
- file or subdir removed
- file removed
for immediate children only (tree walking required?)

- Target dir may start out with or without content. It should be synced so that
it exactly matches the source dir (i.e. delete stuff we dont want).
- Try to minimize writes and message data (task 4 and 5)

- Equality will be checked after each FileSystemEvent trigger.

## Debugging
- FileSystem.debug_string gives a string repr of a FS subtree (dirs and contents).

Increment TASK_NUM in remote_file_replicator.py to activate more tests.

# TODO
1. Initial sync on init. Assume the target dir starts empty. (test_initial_sync and test_unrelated_dirs)

2. Add dir watching so that updates to the source dir get synced.
   Unwatch when no longer needed. (test_watch_dirs and test_unwatch_dirs)

3. Handle non-empty target. Should match exactly. (test_non_empty_target_dir)

4. Minimize file writes: existing files that match are not written (test_avoid_redundant_writes)

5. Reduce data sent in RPCs for large files by ensuring full content is only sent when necessary.
   No test case provided (diff? compression?)
"""

import posixpath
from typing import Any, Callable

from file_system import FileSystem
from file_system import FileSystemEvent

# ALEX: I realize these are meant to be private, but it is confusing that
# the filesystem API gives a public interface that returns these objects,
# and there is no function to determine which one they are. So, I could try
# to access members within a try-except, but I think its nicer to check the
# instance type. I think this is a design flaw in the API.
# Please let me know if you would like me to demonstrate that I can recursively
# construct an in-memory filesystem instead (I have done the leetcode problem
# many times - maybe that is what you are looking for?)
from file_system_impl import _File as File, _Directory as Directory

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