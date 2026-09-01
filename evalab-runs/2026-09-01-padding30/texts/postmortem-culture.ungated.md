**Let's stop asking who broke it**

Last month's checkout outage took four hours to resolve and about twenty minutes of that was spent figuring out who had pushed the config change. That's the part I want to talk about.

I'm not arguing we go soft on quality. I'm arguing the opposite. Right now, when something breaks, the honest answer — "I didn't know that flag applied to prod" — is the answer that gets you a difficult conversation with your lead. So people don't give it. They give the version that makes them look careful, and we write that version down, and six months later somebody makes the same mistake because the real cause never got recorded.

A blameless postmortem is a narrow, boring commitment: the writeup names systems, not people. No "Priya deployed without checking." Instead: "the deploy tool accepted a staging config for a prod target without warning." Same event. One of those you can fix.

The cost is close to zero. We already write incident notes. This changes the pronouns and adds one rule — every action item has to be a change to a system, a check, a default, or a doc. Not "be more careful."

What we get is people volunteering the embarrassing detail, which is almost always the useful one.

I'd like to try it on the next three incidents of any size and compare the writeups to the last three. If the new ones are vaguer or less actionable, we drop it and I'll say so.

Who wants to run the first one with me?
