# Copyright Exafunction, Inc.

"""Remote file replicator between a source and target directory."""

import posixpath
import abc

from typing import Any, Callable, List, Optional

from file_system import FileSystem
from file_system import FileSystemEvent, FileSystemEventType
from file_system_impl import _Directory as Directory, _File as File

from enum import Enum
from dataclasses import dataclass

# If you're completing this task in an online assessment, you can increment this
# constant to enable more unit tests relevant to the task you are on (1-5).
TASK_NUM = 1


class SyncStatus(Enum):
    OK = "ok"
    # TODO: Could also add capacity_depleted, not_found, etc


@dataclass
class SyncRequest:
    updates: List["FileSystemUpdate"]


@dataclass
class SyncResponse:
    status: SyncStatus

    @classmethod
    def ok(cls):
        return cls(SyncStatus.OK)


@dataclass
class FileSystemUpdate(abc.ABC):
    @abc.abstractmethod
    def apply(self, fs, root):
        raise NotImplementedError(
            "apply not implemented"
        )  # TODO: Make own exceptions and return appropriate status


class AddFileOrSubdir(FileSystemUpdate):
    def __init__(self, path, file_content=None):
        self._path = path
        self._file_content = file_content

    def apply(self, fs, root):
        abs_path = posixpath.join(root, self._path)
        if self._file_content is None:
            fs.makedirs(abs_path)
        else:
            fs.writefile(abs_path, self._file_content)

    def __repr__(self):
        content_string = f', "{self._file_content}"' if self._file_content else ""
        return f'AddFileOrSubdir("{self._path}"{content_string})'


class RemoveFileOrSubdir(FileSystemUpdate):
    def __init__(self, path):
        self._path = path

    def apply(self, fs, root):
        abs_path = posixpath.join(root, self._path)
        assert abs_path in fs._objs
        
        print(">>> REMOVE: ", abs_path)
        if not fs.exists(abs_path): return
        if fs.isdir(abs_path):
            fs.removedir(abs_path)
        elif fs.isfile(abs_path):
            fs.removefile(abs_path)

    def __repr__(self):
        return f'RemoveFileOrSubdir("{self._path}")'


class ModifyFile(FileSystemUpdate):
    # TODO: Calculate and apply diffs instead of overwriting
    def __init__(self, path, file_content):
        self._path = path
        self._file_content = file_content

    def apply(self, fs, root):
        abs_path = posixpath.join(root, self._path)
        if not fs.isfile(abs_path):
            raise Exception("Path is not a file")
        fs.writefile(abs_path, self._file_content)

    def __repr__(self):
        return f'ModifyFile("{self._path}", "{self._file_content}")'


def create_initial_updates(fs, root):
    for path, obj in fs.get_dir_objs(root).items():
        if path == ".":
            continue
        if isinstance(obj, Directory):
            yield AddFileOrSubdir(path)
            yield from create_initial_updates(fs, path)
        elif isinstance(obj, File):
            yield AddFileOrSubdir(path, obj.content)


def create_update(root, event):
    print(">>> ORIGINAL UPDATE PATH:", event.path)
    assert event.path.startswith(root)
    path = posixpath.relpath(event.path, root)
    print(">>> UPDATE PATH:", path)

    if event.event_type == FileSystemEventType.FILE_OR_SUBDIR_REMOVED:
        return RemoveFileOrSubdir(path)


class ReplicatorSource:
    """Class representing the source side of a file replicator."""

    def __init__(self, fs: FileSystem, dir_path: str, rpc_handle: Callable[[Any], Any]):
        self._fs = fs
        self._dir_path = dir_path
        self._rpc_handle = rpc_handle
        self._initial_sync()
        self._setup_watch()

    def debug_string(self):
        return self._fs.debug_string(self._dir_path)

    def _objects(self):
        return self._fs.get_dir_objs(self._dir_path)

    def _initial_sync(self):
        updates = list(create_initial_updates(self._fs, self._dir_path))
        self._send(updates)

    def _send(self, updates):
        return self._rpc_handle(SyncRequest(list(updates)))

    def _setup_watch(self):
        # TODO: Do this recursively
        self._fs.watchdir(self._dir_path, self.handle_event)

    def handle_event(self, event: FileSystemEvent):
        """Handle a file system event.

        Used as the callback provided to FileSystem.watchdir().
        """
        print("\n>>> RECEIVED EVENT:", event)
        self._send([create_update(self._dir_path, event)])


class ReplicatorTarget:
    """Class representing the target side of a file replicator."""

    def __init__(self, fs: FileSystem, dir_path: str):
        self._fs = fs
        self._dir_path = dir_path
    
    def debug_string(self):
        return self._fs.debug_string(self._dir_path)

    def _objects(self):
        return self._fs.get_dir_objs(self._dir_path)
    
    def handle_request(self, request: Any) -> Any:
        """Handle a request from the ReplicatorSource."""
        print()
        print(">>> HANDLING REQUEST!")
        print(">>> OLD OBJECTS: ", self._objects())
        print(self.debug_string())
        # TODO
        for update in request.updates:
            update.apply(self._fs, self._dir_path)
        
        print(">>> NEW OBJECTS: ", self._objects())
        print(self.debug_string())
        
        return SyncResponse.ok()
