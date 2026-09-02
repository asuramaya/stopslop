**Our incident reviews are finding people. They should be finding causes.**

Three weeks ago a config push took checkout down for 40 minutes. The review identified who pushed it. What it never got to was why one unreviewed config change can take checkout down at all, or why the rollback took 26 of those 40 minutes.

That's the trade we're making, and it's a bad one. When the outcome of a review is a name, everyone in the room learns to protect themselves. Timelines get vaguer. "I wasn't sure, so I guessed" turns into "I followed the runbook." Near-misses stop getting reported, because reporting one costs you something and buys you nothing. We end up with tidy documents and a system we understand less well every quarter.

Blameless doesn't mean nobody is accountable. It moves accountability off the person who happened to be holding the pager and onto the fixes: named owners, dates, tracked like any other work. Someone still answers for whether the guardrail ships.

Concretely, I'd like to try four things on our next Sev-2:

- A facilitator from outside the affected team.
- A factual timeline written and agreed before anyone offers analysis.
- Roles in the document, not names. "The on-call engineer," not Priya.
- Action items with an owner and a date, reviewed at the next ops sync.

None of this is expensive. It costs one person's afternoon and some discomfort about dropping the part where we identify the responsible party.

I'll run the next one this way if nobody objects. Tell me what I'm missing.
