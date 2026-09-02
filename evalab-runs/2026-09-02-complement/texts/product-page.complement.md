# Threadline

Team chat that keeps engineering context where the work happens.

Most chat tools treat every message the same. Threadline separates the ambient stream from decisions your team needs six months from now. Any message can be promoted to a decision record: it gets a title, an owner, and a permanent link that survives channel archiving.

**What you get**

Channels scoped to services, not vibes. A channel can be bound to a repository, so pull requests, deploy events, and incident alerts land in the same place as the conversation about them. New engineers read one channel and understand one system.

Threaded replies that stay threaded. Replies never leak into the main channel. Long threads collapse to a summary line with participant count and last activity, so a busy channel stays readable during an incident.

Search that knows about code. Paste a stack trace and Threadline matches it against previous occurrences across your workspace, including messages in private channels you have access to. Search filters on author, repository, time range, and whether a thread produced a decision.

Retention you control per channel. Set incident channels to keep everything and standup channels to expire in 30 days. Compliance exports run to S3 in JSON.

Self-hosting on Kubernetes, or our managed cloud in us-east, eu-west, and ap-southeast. SSO through Okta, Entra, or any SAML 2.0 provider. SCIM provisioning on all paid tiers.

Pricing is per active user per month, billed on the count of people who actually posted. Quiet months cost less.

Start a 30-day trial with your existing directory. Migration tooling imports Slack and Discord history, including files and threads.
