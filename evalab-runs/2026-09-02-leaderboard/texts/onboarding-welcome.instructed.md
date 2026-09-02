# Welcome

You made it. Your laptop is on your desk, your accounts are provisioned, and someone will come find you around 10 to get coffee.

Here's what the first day actually looks like. Morning is setup: clone the monorepo, run `./bin/bootstrap`, and let it churn for twenty minutes. It will fail at least once on the Postgres step. That's normal, and the fix is in `docs/onboarding/troubleshooting.md`. If it's still broken after two tries, ask in #eng-help instead of grinding on it alone. Nobody here scores points for suffering quietly.

After lunch, your onboarding buddy will walk you through the service map. Don't try to memorize it. Three services matter for your first month, and you'll learn the rest by accident.

Your first pull request should land this week. It doesn't have to be interesting. Fix a typo in a log message, delete a dead config flag, tighten a test. The point is to get through the full loop once while someone is watching who can help: branch, PR, review, CI, deploy. Once you've done it, the rest is repetition.

A few things about how we work. Code review is a conversation, not a gate. We deploy on Fridays, because if we can't deploy on a Friday, something is wrong with the pipeline and we'd rather find out. Meetings have agendas or they get cancelled. On-call starts at month three, never sooner.

One request: keep notes on everything that confused you this week. In six weeks you'll have stopped noticing, and those notes are the best onboarding docs we have.

Glad you're here.
