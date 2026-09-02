Technical debt is the thing everyone agrees is a problem and nobody schedules. This month we stopped talking about it in the abstract and went looking for it.

Three teams took a week each to write down what actually slows them down. The answers were not what the roadmap assumed. Payments expected the ORM layer to top the list; instead it was the deploy script, a 400-line shell file that four people can read and two are willing to touch. Search found their slowest work sat in test fixtures that take eleven minutes to rebuild. Platform found nothing surprising at all, which is its own finding, and worth reading about on page 6.

Inside: Priya walks through the migration off the legacy job queue, including the two weeks we lost to a retry semantic nobody had documented. Marcus makes the case for a standing 10% budget and shows the numbers from the quarter we tried it. And we have a short piece on writing debt tickets that survive triage, since most of ours currently do not.

One thread runs through all of it. Debt gets paid down when someone can name the specific cost in hours, not when the codebase feels bad. Start there.
