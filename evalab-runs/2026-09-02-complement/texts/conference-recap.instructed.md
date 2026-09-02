Notes from three days at the conference

Four of us went. We split up for most of the talks and compared notes over dinner, which turned out to be the useful part.

The thing that came up in almost every hallway conversation was cost. Two years ago the questions were about scale and latency. This year people wanted to know what their observability bill was and whether anyone had gotten it down. One team from a mid-size fintech described cutting their trace volume by 80% with head-based sampling and finding that their on-call debugging did not get meaningfully worse. We are going to try a scaled-down version of that on one service next month and see if the same holds.

The vendor floor was less interesting than the birds-of-a-feather sessions. In the one on incident review, about half the room admitted they write postmortems that nobody reads. That matched our experience. Someone suggested capping them at one page and requiring a named owner for each action item, with a date. We already do the owner part. The one-page cap is worth trying.

A talk on schema migrations by Priya Raghavan at Stripe was the single best hour any of us spent. Her argument: the expand-contract pattern fails not on the technical steps but on the contract phase, because nobody wants to own deleting the old column. Assign that as a ticket at the start, not the end.

Slides for the three talks we thought were worth your time are in the shared drive folder. Happy to walk anyone through the sampling change.
