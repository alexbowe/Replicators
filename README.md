# CodeiumOA

This is the question from a Codeium Online Assessment.

Here is an abbreviated version of the question:

Question (rough notes, not exact text):

# Requirements
- Replicator for directories (one machine to another)
- When any changes occur on the source machine, sync to target machine
- While they are copying, nothing else will be modifying

## Replicators
- ReplicatorSource and ReplicatorTarget
- Both access their respective directory.
- Communicate with RPC (Source calls functions on Target)

## Communication
- ReplicatorSource can call its `self._rpc_handle` function
  which corresponds to calling `handle_request` on the Target.
- Must define request and response types.
- Both must be pickleable py objects (python stdlib stuff is usually pickleable)

## Filesystem API
- See `file_system.py`
- posixpath.join, posixpath.basename, posixpath.dirname, posixpath.relpath
  (posixpath is like os.path but works on Windows) - dont use os.path! Mock FS
- ReplicatorSource can also ask the filesystem to watch for changes
  using a callback whenever FS has events: `self._fs.watchdir(dir_path, self.handle_event)`
- Watching a dir consumes valuable system resource, so remove them if they are
  no longer needed: `self._fs.unwatchdir(dir_path)`

For each dir, three kinds of file system events:
- file or subdir added
- file or subdir removed
- file removed
for immediate children only

- Target dir may start out with or without content. It should be synced so that
it exactly matches the source dir (i.e. delete stuff we dont want).
- Try to minimize writes and message data (task 4 and 5)

- Equality will be checked after each FileSystemEvent trigger.

## Debugging
- FileSystem.debug_string gives a string repr of a FS subtree (dirs and contents).

Increment TASK_NUM in remote_file_replicator.py to activate more tests.

# Tasks

|# | Task | Test |
|--|------|------|
|1|Initial sync on init. Assume the target dir starts empty|`test_initial_sync`, `test_unrelated_dirs`|
|2|Add dir watching so that updates to the source dir get synced. Unwatch when no longer needed.| `test_watch_dirs`, `test_unwatch_dirs`|
|3|Handle non-empty target. Should match exactly.| `test_non_empty_target_dir`|
|4|Minimize file writes: existing files that match are not written| `test_avoid_redundant_writes` |
|5|Reduce data sent in RPCs for large files by ensuring full content is only sent when necessary. | No test case provided - reviewed by humans |