Draft below — 252 words, clean through the slopwatch gate.

---

At 3:14 a.m. the checkout service starts returning 500s. Your dashboard is green. Every host is up, CPU sits at 12%, the load balancer reports healthy targets, and somewhere a customer is writing a support ticket that will reach you in six hours.

That gap is the whole argument. Everything you thought to measure looks fine, and the thing you actually care about is broken.

The word "observability" has been flattened by vendor marketing, so let's start with what it isn't. It isn't a dashboard. It isn't three tools sold in a bundle and called pillars. Observability is a property of your system: can you answer a question you didn't think to ask in advance, without shipping new code to answer it?

That last clause is where most teams fall down. Monitoring handles the failures you predicted. You knew disks fill up, so you alerted on disk. But the incident that wakes you at 3 a.m. is, almost by definition, the one nobody predicted: a retry storm from a client you forgot existed, or a p99 that degrades only for Android users in São Paulo between 9 and 11 a.m.

You cannot pre-build a dashboard for that. You can only build a system that lets you ask.

The payoff isn't fewer incidents. Incidents are the cost of shipping. The payoff is that the median one closes in eleven minutes instead of ninety, because the on-call engineer spent that time reading data rather than guessing which of forty services to SSH into first.

---

Two numbers are invented placeholders — the eleven-vs-ninety minute MTTR figures. Swap in your own data or cut the sentence to "closes in minutes instead of hours." The opening timestamp and 12% CPU are scene-setting and read fine as fiction.
