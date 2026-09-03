# Welcome to payments

You are joining the team that moves money. Everything else in the product can fail and be retried later; a payment that fails halfway leaves someone short. That constraint shapes most of the decisions you will find odd at first, and it is worth holding onto when a review comment seems pedantic.

## What we own

Three services. `ledger` is the double-entry record and the source of truth for every balance. `gateway` talks to the four processors we integrate with and normalizes their wildly different failure modes. `payouts` batches and schedules outbound transfers, including the retry logic for bank rejections. You will spend your first weeks in `gateway`, because it teaches you the domain fastest.

## Rules we do not bend

Every write to the ledger is append-only. Corrections are new entries.

Every external call carries an idempotency key, and every handler must tolerate being called twice with the same one, because processors do resend webhooks.

Never log a full card number or bank account. That includes debug level on your own machine. Our redaction middleware catches most of it, and we still find leaks in code review, usually in a hand-rolled log line someone added while chasing a bug.

## Your first week

Get the local stack running (see `docs/local-setup.md`), then pair with your onboarding buddy on a small `gateway` ticket. Ask about anything that looks arbitrary. Usually there is an incident behind it.

## Who to ask for what

Priya wrote most of `ledger`. Take reconciliation questions to her before you write a migration, and expect a longer answer than you wanted about why a balance query that looks simple is not.

Dan owns the processor relationships. If a processor returns something the docs do not mention, he has probably already emailed them about it.

Sam handles the payouts schedule and the bank file formats. Cutoff times, holidays, a transfer that left but never arrived: start with Sam.

For access, credentials, or a broken local environment, post in `#payments-help` rather than DMing. Someone else has usually hit the same thing that week, and the answer stays searchable instead of dying in a thread only the two of you can read.

Anything touching PCI scope goes to `#payments-compliance` first. That includes a new request field that might carry card data.

## On-call

The rotation is one week, one person, handed over Tuesday mornings. You will not be added to it for at least two months, and your first two rotations are shadowed by someone who has done it before. Pages come from `#payments-alerts`, and the runbooks live in `docs/runbooks/`. Read them before your shadow week, not during it.
