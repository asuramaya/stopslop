**Interest, Compounding**

Nobody sets out to write bad code. Debt arrives the way it does in ordinary life: one reasonable decision made under pressure, then another, and then the interest payments start.

This month we're looking at the parts of the codebase we quietly apologize for. Not the disasters. The ordinary stuff. The service that works fine right up until you need to change it. The config file with a comment from 2021 that says "temporary." The flaky test everyone reruns twice because nobody has an afternoon to spare finding out why.

Inside, three engineers write about paying some of it down. One rebuilt a deploy path that had grown seven conditional branches, none of which anyone could explain. One argues we should stop calling it debt at all, since the metaphor lets us pretend there's a payment schedule. And one makes the case for leaving a mess alone: the code is ugly, it hasn't changed in four years, and touching it buys us nothing.

We don't expect you to agree with all three. We didn't. But the argument itself is the useful part, and it's one worth having out loud rather than in the review comments at 6pm on a Friday.
