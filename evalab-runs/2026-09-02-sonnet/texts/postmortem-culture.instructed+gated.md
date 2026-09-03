We ship bugs. Last quarter's outage took down checkout for 40 minutes because a config change went out without a canary. That's the kind of thing worth writing up, and right now we don't have a format for doing it.

I want us to start running blameless postmortems for incidents above a certain severity. A postmortem covers what happened, what the systems and process allowed to happen, and what we change so it can't happen the same way twice. It does not name who pushed the change or ask why they didn't catch it.

When a postmortem points at a person, two things happen. People stop reporting their own mistakes early, when they're cheapest to fix. And the write-up stops at "so-and-so should have checked" instead of asking why the system let one person's unchecked action reach production. Neither outcome makes the next incident less likely.

Google's SRE book documents this from over a decade of incident reviews: teams that remove blame get more complete incident reports and find more systemic fixes, because engineers describe what they saw instead of building a defense.

Here's what I'm proposing. Every incident above severity 2 gets a written postmortem within 5 business days, using a shared template: timeline, impact, root cause, action items with owners and dates. No names attached to mistakes in the doc. The review meeting is open to anyone who wants to attend, not just the people involved.

This costs us a few hours per incident. It's cheap next to a repeat of an outage we already paid for once.

Reply here if you want to co-own the first one, or if you think a different severity threshold makes more sense.
