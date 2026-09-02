Stop putting names in outage reports

Our last incident writeup named a person in the second paragraph. It never got around to why the deploy tool let a single command drain a production pool with no confirmation step. We found a culprit and lost the bug. That's the trade blame makes. It feels like accountability, and it buys you silence.

I want us to adopt blameless postmortems, the practice rather than the word. In practice the writeup describes what the system made easy, what information the on-call actually had at 3am, and which guardrail was missing. Nobody's name appears next to a mistake. The question is never who ran the command but why running it was possible at all.

The objection I expect is that this lets people off the hook. It doesn't. Blameless postmortems are strict about systems and generous about people, and the strictness is the point. A reviewer who can't blame Sarah has to go find the real defect, which is harder and more useful.

There's a selfish argument too. Right now people route around incidents. They fix quietly, they downplay, they wait to see if anyone noticed. Every hour of that is an hour we're not learning.

Google, Etsy, and roughly everyone who runs infrastructure at scale figured this out a decade ago, and the reason is boring. Engineers report more when reporting is safe.

I'll draft a template and run the next incident this way. If the writeup is worse than what we do today, we go back.
