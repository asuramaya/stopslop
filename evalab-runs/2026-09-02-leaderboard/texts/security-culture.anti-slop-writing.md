**Nobody on the security team writes your code**

Priya, Wole, and Tomás cover four hundred engineers between them. Do that math, then ask why we keep filing security as somebody else's ticket.

In March someone on billing opened a DocuSign lookalike. Good one, too. I read the same email and hovered over the link for maybe three seconds before the sender domain felt wrong. Three seconds isn't a security program. That's luck.

What I'm asking for isn't heroic. Four things.

Report the weird thing. If an email, a Slack DM, or a build step looks off, hit the phish button or drop it in #sec-triage. False alarms cost us nothing. We got 61 reports last quarter, 9 were real, and I'll take that ratio forever.

Read your own dependencies. When you add a package, look at who maintains it and when they last shipped. Two minutes.

Threat-model in the design doc, not after. One paragraph. What data does this touch, who can reach it, what breaks if the token leaks.

Stop pasting credentials into Slack. I know. Still happening.

Priya's team can't review every PR and shouldn't. They're the people who know the hard parts, the auth flows, the crypto, the places where being clever gets you owned. Save them for that. Every hour they spend telling us our S3 bucket is public is an hour they aren't spending on the stuff only they can do.

And if you're unsure whether something counts as a security question, it does. Ask anyway.
