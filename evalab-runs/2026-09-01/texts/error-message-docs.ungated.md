Note: that exact string isn't emitted anywhere in this repo (the dashboard's flock in `src/dashboard_launch.py:199` fails silently), so here's the entry written generically. Tell me the tool and lock path and I'll pin it to specifics.

---

## `error: lock held by another process`

The tool takes an exclusive lock before it writes, so two copies never edit the same state at the same time. This message means the lock was already taken when your run asked for it. Your run stopped before touching anything, so nothing was written and nothing is corrupted.

Two situations produce it.

**Another run is still going.** A second terminal, an editor plugin, a CI job, or a hook that fires on save may hold the lock. Find it with `ps aux | grep <tool>`. If the work is short, wait for it to finish and run your command again. If it is a long job you did not intend to start, stop that process and retry.

**A previous run died without releasing the lock.** A `kill -9`, a closed terminal, or a machine that lost power leaves the lock file behind with no owner. Read the PID in the lock file and check whether that process still exists. If it does not, delete the lock file and run the command again.

Delete the lock file only after you have confirmed no live process owns it. Removing it while a run is active lets two writers collide, which is the failure the lock exists to prevent.
