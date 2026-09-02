# Kettle

Kettle is a team chat application built around threads that have an owner and a state, rather than channels that scroll.

When someone opens a thread in #payments, it gets a name and lands in a list. It stays there until someone marks it resolved. As a manager, that means you can see the fourteen things your team is currently holding without running a standup or asking for updates in a DM.

## What changes day to day

Decisions stop dissolving into channel noise. A resolved thread keeps a one-line outcome and drops out of the active list, so the reason you picked Postgres over DynamoDB is a search away instead of buried in 400 messages from March.

Handoffs across time zones stop losing state. The thread carries its own history, so the person in Berlin picking up a production issue at 08:00 reads the thread, not a summary someone had to write at midnight.

## The parts you will ask about

Search covers messages, thread outcomes, and file contents, and returns results in under 400ms on workspaces up to 50,000 threads. Slack import brings channels, history, and file attachments; a 3-year workspace typically finishes in under an hour. There are webhooks in both directions, a REST API, and a CLI. SSO through Okta, Google, and Entra ID is on every paid plan, not gated behind an enterprise tier.

## Pricing

$7 per user per month. Free for teams under 10 people. No message history limits at any tier.

Start a workspace, import your Slack export, and see whether the thread model holds up against a week of your team's actual traffic.
