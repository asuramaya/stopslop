# Thread

Team chat that keeps engineering context where the work happens.

Most chat tools treat every message the same. Thread separates ambient conversation from decisions. Any message can be promoted to a decision record with two keystrokes; it gets a permanent URL, an owner, and a date, and it stays searchable after the channel scrolls past it. When someone asks in six months why you picked Postgres over DynamoDB, the answer is one search away instead of lost in a thread nobody remembers.

## What you get that Slack does not

Search covers message history with no retention cap on paid plans. Free-tier limits are the reason most teams lose their own archive, so we removed the limit rather than tiering it.

Incident mode turns a channel into a timeline: every message is timestamped against the incident start, status changes are pinned to the header, and the export is a Markdown postmortem draft rather than a transcript dump.

Code blocks render with syntax highlighting for 40 languages and link to the file in GitHub, GitLab, or Bitbucket when the repo is connected. Stack traces collapse by default and expand inline.

## Pricing

$7 per user per month, billed annually. No separate tier for search, SSO, or audit logs. SCIM provisioning is included.

## Migration

The Slack importer brings over channels, threads, files, and user mappings. A 200-person workspace takes about 40 minutes. Members keep their handles, and old permalinks redirect.

Start a 30-day trial without a credit card. If you are evaluating against Slack or Teams, we will run the import into a sandbox workspace so you can compare on your own history.
