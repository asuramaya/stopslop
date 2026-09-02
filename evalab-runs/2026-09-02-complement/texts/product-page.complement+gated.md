# Fathom

Chat for teams that ship code.

Your team already has a chat tool. The question is what it costs you in attention. Fathom is built around the idea that most messages can wait, and the ones that can't should be obvious.

Every reply lands in a thread, so channels stay readable a week later and a new hire can reconstruct why you picked Postgres over DynamoDB without asking anyone. You write the escalation rules yourself, and a channel can notify only on the words that matter to you, your service names, your alert prefixes, your own handle. Everything else waits for you to open the app. On-call rotations pull from PagerDuty, so the person paged is the person actually holding the pager.

Code renders like code. Syntax highlighting for 40 languages, diffs that fold, stack traces that collapse to the first ten frames.

Paste a 400-line log without burying the channel. Fathom connects to GitHub, GitLab, Linear, Jira, Sentry, Datadog, and a REST API with a documented rate limit. Self-hosted deployment ships as a single container with Postgres and S3-compatible storage. Search covers message history, uploaded files, and thread titles, with results in under 200ms on workspaces up to 50,000 users. Retention is per-channel, and admins can set legal hold without freezing everyone.

Pricing is $7 per user per month, billed annually. Self-hosted is $9. SSO, audit logs, and the API are included at both prices, with no separate tier.

Trial runs 30 days, no card. Import from Slack takes about an hour for a 100-person workspace.
