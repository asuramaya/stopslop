**Subject: One quarter of engineering time to pay down debt in [system]**

**The ask.** For Q[X], I want to flip our split from roughly 90/10 feature-to-maintenance work to 70/30, dedicated to three specific problems. This is not open-ended cleanup. It has a scope, a definition of done, and an end date.

**Why now.** [N] of our last [M] incidents traced back to the same three places: [shared mutable config in the payments service], [the untyped ingest path], and [the release pipeline]. We keep routing around them. Any feature touching [system] now runs two to three times its estimate, and most of that overrun goes to re-reading code nobody owns.

**What we'd do.**
1. [Extract config into a typed, validated module] — done when [service boots fail loudly on bad config instead of at 3am].
2. [Add contract tests to the ingest path] — done when [a schema change breaks CI, not production].
3. [Cut release time from 40 minutes to under 10] — done when [we can ship twice a day without a war room].

**What it costs.** [Feature A] slips one quarter. [Feature B] ships without [the reporting view]. I'd rather name those trade-offs now than discover them in October.

**How we'd know it worked.** Incident count in [system], median cycle time for changes touching it, and estimate accuracy. I'll report all three at the end of the quarter, including if the numbers don't move.

**If we don't.** The interest keeps compounding. We're already paying it — in slipped dates and on-call attrition — we just aren't calling it that on any roadmap.

Happy to walk through the details with anyone who wants them.
