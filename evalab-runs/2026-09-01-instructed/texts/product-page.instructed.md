# Relay

Chat for engineering teams, built so that the conversation and the work stay attached to each other.

## Threads that survive the week

Every thread has an owner and a state: open, waiting, or closed. A thread nobody has touched in three days shows up in the owner's morning digest, not in a channel nobody reads. When it closes, the resolution stays pinned at the top, so the next person who searches finds the answer instead of the argument.

## Search that covers the whole trail

Relay indexes messages, uploaded files, code snippets, and linked pull requests together. Searching an error string returns the incident thread, the Grafana screenshot someone pasted, and the PR that fixed it, in one result list.

## Incidents without a second tool

Type `/incident` and Relay opens a channel, pages the on-call from PagerDuty or Opsgenie, starts a timestamped log, and writes a timeline you can export as Markdown when you run the postmortem.

## What it costs and what you get

$7 per user per month, billed annually. Unlimited history on every plan — we do not gate search behind a tier. SAML SSO and SCIM provisioning are included, not an enterprise upsell.

## What it does not do

No video calls. No document editor. No app marketplace. Relay integrates with GitHub, GitLab, Jira, Linear, PagerDuty, Opsgenie, Sentry, and Datadog, and we keep that list short so each one works properly.

Import your Slack workspace with the CLI, keep the message history, and run both in parallel for as long as you need.
