# Cabana

Team chat built around the systems your team already runs.

Most chat products are sold to a whole company and handed to engineering last. Cabana works the other way. A channel can be bound to a service, so its deploys, alerts, and on-call handoffs land in the same place people are already talking. When someone pastes a pull request link, it expands into review state and CI status, and it updates in place when that changes.

Threads are the default, not an option buried in a hover menu. Every thread can be closed with a resolution, and closed threads stay searchable with their decision attached. Search covers messages, thread resolutions, and the files people uploaded, and it respects channel permissions rather than quietly indexing past them.

## What managers usually ask about

Admin controls: SAML SSO, SCIM provisioning, per-channel retention from 30 days to indefinite, and an audit log exported to your SIEM over webhook. Data residency in US, EU, or Australia. A self-hosted build ships as a single container with Postgres.

Migration from Slack or Teams imports channel history, threads, and file attachments. A 4,000-person migration takes about six hours; we run it against a staging workspace first so you can check what survived.

Pricing is $7 per user per month, billed annually, with no separate tier for SSO. Guest accounts from partner companies are free.

## Where Cabana is a poor fit

If your organization runs most of its work through documents and spreadsheets rather than repositories and incidents, the service-centric model gets in the way. Confluence-shaped teams are better served elsewhere.

Start a 30-day trial, or ask for a migration dry run.
