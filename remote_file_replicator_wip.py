# Copyright Exafunction, Inc.

"""Remote file replicator between a source and target directory."""

"""
Personal Notes

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
- posxpath.join, posixpath.basename, dirname, relpath
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
from file_system import FileSystemEventType

from enum import Enum

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


class SyncStatus(Enum):
    OK = "ok"


class SyncRequest:
    def __init__(self, sync_data):
        self._sync_data = sync_data

    @property
    def sync_data(self):
        return self._sync_data


class SyncResponse:
    def __init__(self, status: SyncStatus):
        self._status = status

    @classmethod
    def ok(cls):
        return cls(SyncStatus.OK)

    @property
    def status(self) -> SyncStatus:
        return self._status

def remove(fs, path):
    """Remove a file or directory from the filesystem without complaining if it doesnt exist"""
    try:
        if fs.isdir(path):
            fs.removedir(path)
        elif fs.isfile(path):
            fs.removefile(path)
    except:
        return

def reset_dir(fs, root):
    for path, _ in fs.get_dir_objs(root).items():
        remove(fs, path)
        

"""
def split_path(path):
    return [x for x in path.split("/") if x]


def walk(fs, root):
    for path, obj in fs.get_dir_objs(root):
        if isinstance(obj, Directory):
            walk(fs, path)
        elif isinstance(obj, File):
            print(path, obj.content)

class FileTree:
    def __init__(self):
        self._tree = defaultdict(FileTree)
        self._content = None # Text if this is a file
    
    def _find_tokens(self, tokens):
        if not tokens: return self
        returns self._tree[tokens[0]]._find_tokens(tokens[1:])
        
    def find(self, path):
        tokens = split_path(path)
        return self._find_tokens(tokens)
    
    def mkdir(self, path):
        return self.find(path)
    
    def sync_from(self, root):
        pass
    
    def sync_to(self, root):
        # Delete files that are not in the tree
        # Delete files that have changed
        pass

    def update(self, event):
        pass

    def add_listener(self, listener):
        pass

    def remove_listeners(self):
        pass

    def __del__(self):
        self.remove_listeners()
    
    def delete(self, path):
        pass
"""


class FileIndex:
    def __init__(self, path):
        self._path = path
        self._listeners = []
    
    def add_listener(self, listener):
        self._listeners.append(listener)


class SyncData:
    def __init__(self, tree):
        self._tree = tree
        self._listeners = dict()

    @property
    def tree(self):
        return self._tree

    @classmethod
    def load_from_path(self, fs, root):
        return SyncData(fs.get_dir_objs(root))

    def sync_to_path(self, fs, root):
        """Sync the tree to the provided path"""
        reset_dir(fs, root) # TODO: Update this to only remove files that have changed.
        for path, obj in self._tree.items():
            abs_path = posixpath.join(root, path)
            if isinstance(obj, Directory):
                fs.makedirs(abs_path)
            elif isinstance(obj, File):
                fs.writefile(abs_path, obj.content)


class ReplicatorSource:
    """Class representing the source side of a file replicator."""

    def __init__(self, fs: FileSystem, dir_path: str, rpc_handle: Callable[[Any], Any]):
        self._fs = fs
        self._dir_path = dir_path
        self._rpc_handle = rpc_handle
        #self._sync_object = None # Store this when we want to minimize updates

        self._sync()
        self._set_up_listeners()

    def _get_sync_object(self):
        return SyncData.load_from_path(self._fs, self._dir_path)

    def _send_request(self, request: Any) -> Any:
        """Send a request to the ReplicatorTarget."""
        return self._rpc_handle(request)

    def _sync(self):
        sync_object = self._get_sync_object()
        request = SyncRequest(sync_object)
        response = self._send_request(request)
        if response.status != SyncStatus.OK:
            raise Exception("Sync failed") # Probably better to log this and retry in production
    
    def _set_up_listeners(self):
        self._fs.watchdir(self._dir_path, self.handle_event)
        for path,obj in self._fs.get_dir_objs(self._dir_path).items():
            if isinstance(obj, Directory):
                abs_path = posixpath.join(self._dir_path, path)
                self._fs.watchdir(abs_path, self.handle_event)
    
    def handle_event(self, event: FileSystemEvent):
        """Handle a file system event.

        Used as the callback provided to FileSystem.watchdir().
        """
        print(">>>>>>>> EVENT:", event)
        if event.event_type == FileSystemEventType.FILE_OR_SUBDIR_REMOVED:
            print(event.path)
            x = self._get_sync_object()
            print(x.tree.keys())
        # TODO: save a SyncData object and call specific update functions
        # on it when appropriate events occur.
        # Eventually for large files we need to represent diffs upon modification
        self._set_up_listeners() # In case we added new directories
        self._sync()


class ReplicatorTarget:
    """Class representing the target side of a file replicator."""

    def __init__(self, fs: FileSystem, dir_path: str):
        self._fs = fs
        self._dir_path = dir_path

    def handle_request(self, request: Any) -> Any:
        """Handle a request from the ReplicatorSource."""
        print("\n>>>>>>>> REQUEST")
        print(request.sync_data.tree.keys())
        request.sync_data.sync_to_path(self._fs, self._dir_path)
        return SyncResponse.ok()

if __name__ == "__main__":
    pass