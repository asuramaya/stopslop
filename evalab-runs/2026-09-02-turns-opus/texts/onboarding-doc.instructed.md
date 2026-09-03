# Welcome to payments

You are joining the team that moves other people's money. That framing matters more than any architecture diagram: a bug here does not degrade a feature, it takes cash out of someone's account or fails to put it back.

## What we own

Four services. `auth-gateway` talks to the card networks and holds the only credentials that can. `ledger` is the double-entry record of every balance change, append-only, no updates or deletes. `payout-runner` batches merchant disbursements nightly. `recon` compares our ledger against bank settlement files each morning and raises breaks a human reads.

## Two rules before you write code

Every mutating endpoint takes an idempotency key. Networks retry, our clients retry, our own queues retry. A charge that runs twice is the failure mode we spend the most engineering time preventing.

Money is stored as integer minor units with an ISO-4217 currency code. Never a float. Never a bare number without its currency. The `Money` type in `common/money` enforces both; use it rather than passing amounts around as primitives.

## Your first week

Day one is access: Okta groups, the Discord server, the sandbox network credentials, read-only production ledger. Day two, run the local stack and push a test charge through `auth-gateway` to settlement. By Friday you should have shipped one small fix from the `good-first-break` queue in Jira.

## On-call

One week at a time, primary and secondary, handover Tuesday morning. You do not join the rotation until you have shadowed two full weeks and walked through the runbooks with your buddy, so expect that around month three.

Pages come from PagerDuty and route to `#pay-incident`. The paging alerts are settlement lag, authorisation error rate, and payout batch failure; everything else waits for business hours. Secondary exists so you can wake someone rather than guess at the ledger alone at 3am. Use it.

## Who to ask for what

Ledger schema, double-entry invariants, anything that writes a journal entry: Priya. She wrote most of it and reviews every migration against it, so bring her the design before the pull request.

Card network behaviour, declines, 3DS, why a specific acquirer returned a code nobody recognises: Marcus. He has the network specs and the relationships to escalate.

Payout scheduling, merchant balance holds, and the nightly batch windows: Dede.

Recon breaks, settlement file formats, and the finance team's questions about a number: post in `#pay-recon` rather than sending a direct message. The finance analysts read that channel and often answer before an engineer does.

Access, secrets, staging environments, and CI that will not go green: `#pay-platform`.

If you do not know who owns something, post in `#pay-team` instead of guessing. Wrong-guess routing costs a day here; asking costs ten minutes.
