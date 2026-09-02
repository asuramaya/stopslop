Welcome to the September issue. This month we're writing about technical debt, which is a topic everyone at this company has an opinion about and nobody wants to schedule.

The word "debt" does a lot of quiet work in that phrase. Ward Cunningham coined it in 1992 to describe a deliberate trade: ship now against an imperfect model of the domain, pay interest until you refactor. What we usually mean is something looser and less honest — code we don't like, written by people who no longer work here, under constraints we've forgotten. Those are different problems. The first has a payoff date. The second is just archaeology, and it needs a different kind of attention.

So this issue tries to separate them. Priya walks through the auth service migration, including the two weeks we spent discovering that a "temporary" 2021 shim was carrying production traffic for four downstream teams. Marcus has numbers on where our build time actually goes, which surprised him and will probably surprise you: 60% of it sits in one dependency graph nobody has touched since the monorepo split. And we've got a short piece on the debt we chose to keep, and why.

Nothing here is a framework. It's what we found when we looked.
