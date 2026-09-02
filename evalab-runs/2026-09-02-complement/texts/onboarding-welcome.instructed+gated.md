# Welcome

You're here. Someone has already claimed your laptop, set up your accounts, and probably eaten one of your welcome snacks. There are more in the kitchen.

Your first week is not about shipping. It's about getting your bearings. Read this page, then find your onboarding buddy — their name is in the calendar invite for 10am. They'll walk you through the repo, the deploy pipeline, and which Slack channels actually matter (there are four; the rest are noise).

A few things worth knowing up front.

We review every change. Not because we distrust new people, but because we distrust everyone equally, including the person who wrote the deploy script eight years ago and now runs the company. Expect comments on your first PR. That's the system working, and the reviewer who leaves forty of them is not sending you a message about your competence. Read them, push a fix, move on. The comment thread is where most of the actual engineering conversation happens here, so it's also the fastest way to learn how the codebase got the shape it has — why the payments module has that strange retry loop, why nobody touches the migration script on a Friday.

Ask questions early. The cost of a question is two minutes of someone's attention. The cost of quietly guessing wrong for three days is three days. We have a #help channel and nobody has ever been mocked in it.

Break things in staging — that's what it's for. If you take production down in your first month, we'll fix it together and then figure out why the guardrail didn't catch it. Postmortems here are blameless in practice, not just on paper.

Your first commit is expected by Friday. It can be a typo fix in a README. The point is to get through the whole pipeline once — branch, review, merge, deploy — while someone is sitting next to you.

Lunch is at noon. Come find us.
