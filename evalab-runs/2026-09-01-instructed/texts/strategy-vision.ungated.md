## Vision

Two years from now, the complaints we hear from product teams should be different complaints.

Today they're about plumbing: a new service takes three weeks to get to staging, half of which is copying config from whichever repo someone remembers as "the good one." Deploys are a person, not a pipeline. When something breaks at 2am, the first twenty minutes go to finding out which of four dashboards is telling the truth.

The bet we're making is that this work is worth doing centrally, once, rather than in each team badly and repeatedly. Not because platform work is inherently more valuable — it isn't, and no customer has ever asked for a service template — but because we now have enough teams that the duplication is measurable. Six teams solved request tracing independently last year. Four of those solutions are wrong in the same way.

What we want at the end: a new service reaches production in a day, with logging, tracing, secrets, and rollback already attached, because the default path includes them. An engineer who joins in year two learns one deployment story, not seven. The people currently spending a third of their time on infrastructure they didn't choose get that time back.

We should be honest that this trades near-term feature velocity for it. The first six months will feel slow, and some teams will be asked to migrate off tooling that works fine for them today. That cost is real and we're choosing to pay it, because the alternative is paying a larger, quieter version of it every quarter forever.
