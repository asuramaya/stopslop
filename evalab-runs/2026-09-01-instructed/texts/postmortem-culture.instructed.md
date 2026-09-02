We should stop asking who caused an incident

Last quarter's checkout outage review took ninety minutes, and about sixty of those were spent establishing that Marcus pushed the config change. That fact explained nothing. The config change was accepted by a system that let a single-line edit reach production without a staging pass, and that system is what failed.

Every incident review we run right now has a person at the center of it. People know this. So they arrive prepared: they narrow the timeline to what they can defend, they answer questions instead of volunteering context, and they leave out the part where they were unsure but shipped anyway because the deploy window was closing. That last detail is the one worth having, and our current format guarantees we never hear it.

A blameless postmortem means the written record names systems and decisions, not culprits, and no performance consequence attaches to appearing in one. The trade is explicit: we give up the satisfaction of assigning fault, and in return people tell us what actually happened.

I want to try three things. First, a facilitator who does not report to anyone on the responding team. Second, a template where the question is "what made this change look safe?" rather than "who approved it?" Third, action items that must change a system, not a person's habits. "Be more careful" is not an action item.

Google, Etsy, and Stripe have published their versions of this. I'd start with two incidents, compare the write-ups against our last four, and let the difference in detail make the argument. If it doesn't, we drop it.
