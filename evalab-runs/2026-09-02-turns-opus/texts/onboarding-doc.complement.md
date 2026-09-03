## On-call rotation

One engineer holds the primary pager for a week, Wednesday to Wednesday. A secondary picks up anything the primary misses after ten minutes. The handoff happens in a 20-minute call Wednesday morning, where the outgoing primary walks through whatever is still open.

Your rotation starts in week three. Your first two shifts run with a senior engineer shadowing you, and they take over the moment you want them to. Ask.

Most weeks are quiet. The pages that do come are usually a settlement batch failing partner validation or the authorization service running hot on latency. Both have runbooks in `docs/runbooks/`, and if the runbook does not cover what you are seeing, wake the secondary rather than working it alone.
