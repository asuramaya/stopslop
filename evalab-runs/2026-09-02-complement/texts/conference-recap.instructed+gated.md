Four of us went to SREcon last week. Here's what stuck.

The hallway track beat the talks, again. We had three conversations with teams running the same Postgres-to-Kafka pattern we've been fighting, and two of them had already abandoned it. One team at a payments company walked us through why: their change-data-capture lag spiked whenever a batch job touched more than about 200k rows, and no amount of partition tuning fixed it. We've seen the same spike, and we just assumed it was our own configuration. Nobody had written any of this down anywhere we would have found it.

Charity Majors' talk on on-call load included a number we wrote down: a rotation is broken once engineers get paged more than twice per shift. Ours averages five. We'd been treating that as normal because the pages are mostly quick to resolve, and volume felt like the wrong thing to complain about when each individual page cost ten minutes. Quick to resolve is not the same as cheap.

The vendor floor was thinner than last year and the pitches were nearly all agent-shaped. We asked four companies what happens when the model produces a bad remediation at 3am. Only one had an answer that involved a human approval step. The other three described confidence thresholds, which is not the same thing as a person.

Two things we're changing. First, we're pulling the CDC pipeline off the roadmap and spending that quarter on the read-replica approach instead, which two other teams described as boring and working. Second, Priya is auditing six months of pages to see how many were actionable, before we argue about rotation size.

Slides are posted at srecon.usenix.org. The Postgres one is worth the forty minutes.
