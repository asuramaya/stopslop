We should stop ending incident reviews with a name

Someone pushed a config change at 4pm on a Friday and took checkout down for nineteen minutes. You probably know who. That's the problem.

Our reviews currently end with a person. The name goes in the doc, they apologize in the channel, and everyone moves on feeling like something got resolved. Nothing did. The next person to touch that config has the same odds of breaking it, because the config still has no staging path and no confirmation prompt. We corrected a human and left the machine alone.

Blameless doesn't mean nobody is accountable. It means we start from the assumption that everyone acted sensibly given what they knew and what their tools were showing them — and then we go find out what they knew and what their tools were showing them. If a deploy script will cheerfully ship to prod from a dirty branch on a Friday afternoon, someone eventually will. Which someone is the least interesting fact in the incident.

The real payoff is that people stop editing their timelines. You get "I ignored that alert, it fires four times a week" instead of "I investigated the alert." One of those is an action item.

So here is the concrete ask for the next ninety days. Every Sev1 and Sev2 gets a written review inside five working days, facilitated by someone outside the owning team, with roles in the document instead of names. Action items get owners and dates, same as any other work.

If we're not shipping better fixes by January, we drop it.
