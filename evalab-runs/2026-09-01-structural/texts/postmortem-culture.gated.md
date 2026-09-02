Let's run the next incident without naming a culprit

Three weeks ago we lost checkout for 41 minutes. The writeup names one engineer, twice. It never asks why the deploy tool let a config change reach production without a staging pass. That's a bad trade, and I think we've been making it on purpose without noticing.

Here's the mechanism. When a postmortem can end with a person's name attached to it, the cheapest safe move for anyone near the incident is to say less. Nobody lies. They round off, and "there was a config issue" is what lands in the doc. The detail that would have told us the deploy path has no guardrail never gets written down, because volunteering it means volunteering yourself. So the docs get thinner each quarter while the systems they describe get more tangled.

A blameless postmortem is a deal.

You tell us everything you saw, thought, and tried, including the parts that look bad. In exchange, nothing in that doc touches your performance review. It isn't about being nice to each other. It buys the one thing that actually prevents the next outage, which is an accurate account of how a competent person, working from the information in front of them, still ended up doing the wrong thing.

Two objections I expect. "This lets people off the hook." It doesn't, since action items stay mandatory and tracked, and blameless means we fix systems rather than ignore negligence. "Our incidents are too small for this." Good. Small ones are the cheap place to learn the format.

So I'm asking for one trial. We run the next SEV-2 this way, no names in the timeline, and afterward we put that doc next to our last three and compare.
