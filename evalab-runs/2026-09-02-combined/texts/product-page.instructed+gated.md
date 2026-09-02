# Halyard

Team chat for engineering orgs that keep their history.

## Search that covers everything you wrote

Messages, thread replies, uploaded files, and code snippets are indexed together and stay searchable for the life of the workspace. No message tier deletes your backlog after 90 days. When someone asks why a service was built the way it was — why the queue was sharded, why the retry budget is 3 — the answer from 2023 is still there, in the thread where the decision happened, with the people who made it.

## Threads that close

Every thread has an owner and a state. Open threads for your team show up in one list, sorted by age, so a standup takes two minutes instead of a scroll through six channels. Threads you close stop pinging you.

## Incident mode

Type `/incident`. Halyard spins up a channel, pulls in the on-call rotation from PagerDuty or Opsgenie, and timestamps every message into a transcript you can export as Markdown. Postmortem authors get a clean timeline rather than a copy-paste job.

## Integrations you already need

GitHub, GitLab, Linear, Jira, Sentry, Datadog, and a REST API with webhooks. Alert routing supports per-channel filters, so a noisy Datadog monitor does not wake the whole team.

## Administration

SAML SSO and SCIM provisioning on all paid plans, not just enterprise. Audit logs export to S3. Data residency in US, EU, or AU regions. Self-hosting available.

## Pricing

$7 per user per month, billed annually. Guest accounts are free. Security controls are not a separate line item.

Start a 30-day trial, or import your existing Slack export and see how the search holds up.
