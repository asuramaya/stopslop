## error: lock held by another process

The tool keeps one lock file per workspace. Only one process at a time can hold that lock. When a second process asks for a lock that another process already holds, the tool refuses to start and prints this message. Two situations produce it.

**A real concurrent run.** Another copy of the tool operates on the same workspace right now, from a second terminal, an editor plugin, or a scheduled job. Wait for that run to finish. The tool releases the lock when it exits. To confirm, run `tool status --locks`, which prints the process ID and the start time of the holder.

**A stale lock.** A previous run crashed, or the machine lost power, so the tool never released the lock. The lock file survives, but the process behind it no longer exists. If `tool status --locks` reports the holder as `dead`, the lock is stale. Remove it with `tool unlock`. That command checks the recorded process ID first and refuses to act when the process still lives.

Never delete the lock file by hand while a run is alive. Two writers on one workspace corrupt the index, and a rebuild is the only repair.
