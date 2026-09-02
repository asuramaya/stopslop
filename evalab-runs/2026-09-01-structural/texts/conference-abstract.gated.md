Title: We Split the Monolith Twice. The First One Was a Mistake.

We spent fourteen months pulling services out of a Rails monolith, and eight of those months bought us nothing. What we built the first time was a distributed monolith: eleven services that still shared one Postgres database, still deployed together, and now failed in ways no stack trace explained. Latency tripled. On-call got worse.

The second attempt started somewhere less glamorous, with the data. Before we moved a single endpoint, we spent six weeks mapping which tables were actually written by more than one part of the codebase. Four of them. That answer reshaped the whole plan, and it cut the service count from eleven to five.

Both attempts get a walkthrough here. The seams we thought existed turned out to be nothing like the ones the query logs revealed. Our first extraction order ran backwards. The strangler-fig cutover we landed on let us roll back a service in under a minute, and I'll show the two dashboards we watched during each migration, including what a bad one looked like at 2 a.m. You'll leave with a checklist for deciding which pieces to extract first, and a clearer sense of when the answer is to extract nothing at all.

(~205 words. The numbers are placeholders. Swap in your real timeline, service count, and stack, since the specifics are what make it land.)
