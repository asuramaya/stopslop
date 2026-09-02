## `error: lock held by another process`

The tool takes an exclusive lock on its state directory before it writes, so that two runs cannot interleave and corrupt each other. This message means the lock file already exists and something else claims ownership of it.

Two things cause it.

**A second run is genuinely active.** You started the tool twice, or a scheduler, editor plugin, or CI job started it while your shell run was still going.

**The lock is stale.** A previous run died without releasing it — killed with `SIGKILL`, a container stopped, the machine lost power. The file outlives the process that made it.

Tell the two apart by the PID recorded in the lock file:

```
cat .tool/lock        # prints the owning PID
ps -p <pid>           # is it still alive?
```

If `ps` shows a live process and it is this tool, wait for it to finish. Nothing is broken; a second run would have clobbered the first. If you started it by accident, stop the extra one rather than the one doing work.

If `ps` prints nothing, or shows an unrelated process that reused the PID, the lock is stale. Delete the file and run again:

```
rm .tool/lock
```

Check the PID first. Deleting a live lock lets two runs write at once, which is the corruption the lock exists to prevent.
