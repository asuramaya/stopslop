Nomination: Release Engineering, for the Craft Award

Eighteen months ago, shipping to production meant a four-hour Thursday night window, two people on a bridge call, and a rollback plan nobody had tested since March. We released once a week when things went well, once every three weeks when they didn't.

This team rebuilt the pipeline in pieces instead of proposing a rewrite. They started with the rollback path, because that was the part everyone was afraid of. Then the build cache, which took CI from 41 minutes to 9. Then progressive rollout with an automatic abort on error-rate regression, which has stopped 14 bad releases before they reached 2% of traffic.

We now deploy 30 to 40 times a day, in daylight, with no bridge call. Median time from merge to production is 12 minutes.

The number I care about more is the second one: change failure rate went from 18% to 4% over the same period, so the speed didn't come out of anyone's stability budget.

Two things about how they worked. They carried the deploy system's pager themselves for the first two quarters, so every gap hurt the people who could close it. And they documented the blue-green attempt they abandoned with the same care as the parts that shipped, which saved the payments team a quarter of rediscovery.
