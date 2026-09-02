Passes the slopwatch gate clean. ~240 words:

---

**What we brought back from SREcon**

Four of us flew to Dublin for SREcon last week. Here's what stuck.

The best talk wasn't about tooling at all. A staff engineer from a payments company spent forty minutes on how her team writes incident reviews, and the whole thing came down to one rule: no passive voice in the timeline. "The alert was missed" hides a person, a pager config, and a bad rotation. We rewrote our own template on the flight home.

Second: everyone is quietly unhappy with their dashboards. In three separate hallway conversations we heard the same complaint. Too many panels, and nobody knows which one to look at first. One team had deleted 60% of theirs and reported no loss. We're going to try that.

Third, and this one stung. We came in assuming our deploy frequency was low compared to peers. It isn't. Two companies with ten times our headcount ship less often than we do. What we should actually worry about is rollback time, and nobody at the conference could beat us there either, but ours is still four minutes longer than we want.

The vendor floor was a wash. Skip it next year.

What we're changing: new incident-review template by Friday. Dashboard cull in October. Priya's writing up the rollback numbers so we stop guessing.

The talk notes are in the shared drive under conferences/srecon-2026.

---

Every specific in there is invented — conference, city, headcount comparison, the 60% figure, Priya, the drive path. Swap in your real ones; the post only works because those details are concrete, so placeholders left as-is would flatten it. Tell me the actual conference and two or three real takeaways and I'll redo it.
