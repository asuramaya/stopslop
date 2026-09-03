Engineering culture

We ship in small pieces and put them in front of users fast. A feature sits in review for hours, not days, because the person best positioned to catch a problem is the one who just wrote the code, and long queues just delay that feedback.

Every engineer owns their code in production. You write the alert, you carry the pager for it, and you fix what breaks. This keeps the person who understands a system closest to the consequences of its failures.

We review pull requests for correctness and clarity, not style. Formatters and linters settle the arguments that don't need a human. When a review comment turns into a debate, we take it to a call instead of a comment thread.

New hires deploy to production in their first week. The onboarding project is a real bug or a real feature, chosen so the build and review process teaches the codebase along the way.

We hold a two-hour block on Wednesdays with no meetings, for anyone who wants uninterrupted time to write code. Attendance is optional. Most of the team uses it anyway.

Postmortems name the failure, not the person. We ask what the system allowed, not who made the mistake, and we write down the fix we're committing to, with an owner and a date.

We keep a public log of technical decisions, including ones we reversed. If you join a project six months in, the log tells you why the database is Postgres and not something else, and why the first attempt at the queue got scrapped.
