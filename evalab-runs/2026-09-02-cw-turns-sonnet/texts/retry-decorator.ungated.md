The rename is already done — `retry.py` on disk (uncommitted diff by the co-agent, "Ooblek XXIII") already renames `retry` to `with_retries`, updates the call sites, and refreshes the docstring to match (including the `@with_retries(...)` example and the `never_retry` addition). Nothing left to change there.

`retry_exponential.py` still has a function named `retry`, but that's a separate untracked file, not part of this thread's code — I'll leave it alone unless you want it renamed too, since the shared tree has another agent active and I don't want to step on unrelated work.
