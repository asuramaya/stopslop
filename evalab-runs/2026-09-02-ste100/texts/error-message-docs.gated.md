## `error: lock held by another process`

The tool takes an exclusive lock before it writes, so that two runs cannot corrupt the same state. This message means the lock file already exists and the tool refused to touch anything.

There are two reasons you see it.

**Another run is genuinely in progress.** Someone else on the box, a cron job, or a second terminal of your own is mid-write. Wait for it to finish and try again. Check with `ps` or your process manager first. The lock file records the PID that took it, so `cat` it and see whether that process is still alive.

**The lock is stale.** Something sent a previous run `SIGKILL`, or the run lost its container or died with the machine. Either way it never cleaned up. The PID in the lock file will be gone, or reused by something unrelated. Delete the lock file by hand and re-run.

Do not delete the lock as a reflex. If you remove it while the process that holds it still runs, both writers proceed and the state they share ends up interleaved. That is the exact failure the lock exists to prevent, and it is much harder to diagnose than this error. Confirm the PID is dead first.
