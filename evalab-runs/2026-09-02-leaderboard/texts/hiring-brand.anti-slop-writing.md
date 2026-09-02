How we work

Every engineer here has pushed to production in their first week. Not a sandbox, not a feature flag nobody flips. Real traffic.

That's possible because we spent 2023 rebuilding the deploy pipeline after an incident that took our payments API down for four hours on a Tuesday morning in March. Rollback now takes ninety seconds and anyone can trigger it, including the two people who joined last month. We wrote up the whole outage internally, blamelessly, and then we did the boring work of fixing the six things that made it possible.

Code review is where we're most demanding. Reviews get written comments, not thumbs up. If you leave "LGTM" on a 900-line diff, someone will ask you what you actually read. That slows us down some weeks. We think it's the right trade, though I'll admit there are Thursdays when I don't.

We're skeptical of process for its own sake. No sprint planning theater, no story points. Teams of four to six pick their own cadence and defend it at a monthly review. Some run two-week cycles. One team ships continuously and has never once written a ticket.

What we don't have figured out: on-call. It's better than it was, and it's still not good enough. We're honest about that in interviews because you'll find out in month two anyway.

You'll write Go and TypeScript, mostly. You'll read a lot of other people's code. And you'll be expected to have opinions about it, out loud, in writing, where people can disagree with you.
