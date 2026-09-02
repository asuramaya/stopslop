# Chat that respects the work

Your team already has a chat tool. The question is whether it costs you more attention than it saves.

We built this one around a single measurement: how long an engineer stays in a task before something pulls them out. In our own team of 40, moving from an always-on channel model to scheduled digests cut interruptions from 31 a day to 9. That number is the whole design brief, and every default below follows from it.

## What that looks like day to day

Channels have a delivery mode, not a mute button. A channel set to "digest" batches into one notification at times you pick. Incidents override it. Nothing else does.

Threads expire. A thread with no reply in 72 hours closes and drops out of the sidebar. You can reopen it.

Search covers messages, files, and code snippets in one index, with regex support. It returns results in under 400ms on workspaces up to two million messages.

## For the person who owns the decision

Admin controls are per-workspace and scriptable through a REST API. SCIM provisioning, SAML SSO, and audit log export ship on all paid plans, not only enterprise. Data retention is configurable per channel down to 24 hours. Self-hosting is available, as is EU and US data residency on the hosted plan.

Migration imports from Slack, Teams, and Discord preserve threads, reactions, and file attachments. A 500-person import takes about two hours.

## Pricing

$7 per user per month, billed annually. No per-feature tiers. Free for teams under 10. Trials run 30 days without a card. If you want to test the migration first, we will run it against a copy of your workspace so you can see what arrives before you commit.
