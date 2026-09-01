**Documentation entry**

## `error: lock held by another process`

The tool takes an exclusive lock before it writes, so that two runs can't corrupt the same state. This message means the lock was already taken when your command started. There are two reasons that happens.

**Another run is genuinely in progress.** A second terminal, a scheduled job, an editor plugin, or a CI step is using the same working directory. The fix is to wait for it to finish and run your command again. To find it, read the PID from the lock file and check it:

```
cat .toolname/lock      # prints the owning PID
ps -p <PID> -o pid,cmd  # shows what holds it
```

If the process is real, leave it alone. Killing it mid-write is what creates the second case.

**The lock is stale.** The owning process died without cleaning up, usually after a crash, a `kill -9`, or a container that stopped abruptly. `ps` finds nothing for that PID, and no run of the tool is active anywhere. Delete the lock file and retry:

```
rm .toolname/lock
```

Only delete a lock after confirming the PID is gone. Removing a live lock lets two writers touch the same files at once, and the resulting damage is not always visible right away.
