Welcome to the September issue.

We spent most of August paying down interest on decisions nobody in the current team made. The auth middleware, for instance. Written in 2021 by someone who left before I joined, patched eleven times since, and now it's the thing three teams cite when they explain why their feature slipped. Nobody wrote it badly. It just kept being the fastest place to bolt something on.

So that's the theme this month: debt. Not the abstract kind you nod along to in a planning meeting, the specific kind with a filename.

Inside you'll find Priya's writeup of the payments migration (six weeks, one rollback, a graph that will make you wince), a short piece from Devon on why we stopped tracking "tech debt tickets" as a category at all, and some numbers on how much of our on-call volume traces back to two services.

One thing I want to push back on before you read any further. Debt isn't automatically bad. We took on plenty of it deliberately last year to hit a date that actually mattered, and I'd make the same call again. What's bad is debt you've stopped noticing. The stuff that's been in the codebase long enough that people route around it by instinct and nobody remembers there was a road there once.

Go find yours. Write it down somewhere the next person will look.
