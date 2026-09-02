Four of us went to SRECon last week. Here's what stuck.

The talk we expected least from was a 20-minute lightning session on postmortem fatigue. The speaker, an SRE at a mid-size payments company, showed their incident review backlog: 61 open documents, median age 4 months. Their fix was to stop writing full postmortems for anything under Sev-2 and replace them with a three-line entry in a shared log. Their action-item completion rate went from 31% to 74% in two quarters. We have 40-something stale reviews of our own. We're trying their approach starting next sprint.

Two separate teams described the same on-call handoff problem we hit in June, where the outgoing engineer's context lives in Slack threads nobody can find later. Both had landed on a written handoff template pinned to the rotation channel. Neither had automated it. That made us feel better about our own manual version.

The hallway conversations were more useful than three of the five talks we attended. Priya spent 40 minutes with someone from an observability vendor who talked her out of the metrics migration we'd scoped for Q4, on the grounds that our cardinality problem is a naming convention problem and no new backend fixes it.

What we're changing: the postmortem threshold, the handoff template, and shelving the metrics migration pending a naming audit.

What we're not changing: our alerting setup. Three talks pushed toward ML-based alert grouping. Our alert volume is 12 a week. We don't have the problem that solves.

Slides for the postmortem talk are on the conference site. Worth 20 minutes.
