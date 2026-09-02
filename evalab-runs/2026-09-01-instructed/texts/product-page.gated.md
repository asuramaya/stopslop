# Chat that survives your org chart

Halyard is team chat for engineering orgs between 20 and 500 people — the size where your messaging bill starts rivaling your CI bill.

Threads survive reorgs. Move a channel to a new team and its history, pins, and integrations move with it. No archive-and-recreate ritual, no dead links in last quarter's postmortem. Search is one box, not seven: Halyard indexes messages, uploaded files, and linked PRs together, so searching *flaky auth test* returns the thread, the stack trace someone pasted, and the PR that fixed it.

Type `/incident` and Halyard opens a channel, pages the on-call from PagerDuty, and starts a timeline. When you resolve, it hands you a timestamped writeup. Median customer cuts postmortem prep from two hours to twenty minutes.

Compliance isn't an upsell here. Per-channel retention policies, legal hold, SCIM, and SSO come with every plan, including the $7 one.

There are things we deliberately left out. No AI meeting summaries. No stories. No reaction feed ranked by an algorithm. If you want a chat app that also wants to be a social network, buy a different one. Migration, likewise, is boring on purpose: we import Slack history — messages, threads, files, user mapping — on a schedule you pick, and teams under 200 people usually finish over a weekend. Nobody spends a Sunday babysitting a progress bar.

Thirty days free, no card.

Or ask for the security questionnaire first. We send it back the same day, filled in.
