**Your dashboards are green and checkout is still broken**

It's 3 a.m. Payments are failing for something like 4% of carts, every service is reporting healthy, and the on-call engineer is reading logs one grep at a time trying to find a customer who complained on Twitter.

Nobody planned for this. It's what happens when a system gets big enough that no single person holds the whole map in their head anymore, and the tooling was designed back when one person still could. CPU graphs and uptime checks answer a question from 2010: is the box alive? The question that actually costs money is different. *Why is this particular request, from this particular customer, slow right now?*

Monitoring tells you a thing you already thought to worry about has gone wrong. Observability is the ability to ask a question you didn't anticipate — without shipping new code to answer it. That distinction sounds academic until the first time you're twenty minutes into an incident and realize the field you need was never instrumented.

The teams that get this right aren't buying a better dashboard. They're changing what their code emits, so that structured events carry enough context for a human to slice by customer ID, region, feature flag, or the deploy that went out at 2:47. Then the 3 a.m. question takes four minutes instead of four hours.

That's the payoff. Not prettier graphs — shorter incidents, and engineers who trust their own systems enough to sleep.
