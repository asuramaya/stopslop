**Let's stop opening postmortems with "who deployed it"**

We had three incidents last quarter where the write-up named a person in the first paragraph. In two of those, the person had already told their manager before the review started. In the third, we found out what actually happened six weeks later, from someone else, in a hallway.

That's the cost I want to talk about. Not fairness — information. When the review's job is to identify who was careless, people stop volunteering the part where they were confused, or where they clicked through a warning they didn't understand, or where the runbook told them to do the wrong thing and they followed it. Those are exactly the details that tell us how to prevent the next one.

A blameless postmortem isn't a rule against saying names. It's a working assumption: given the information, incentives, and tooling available at 2am, the engineer did something that made sense to them. If that action broke production, the interesting question is why it made sense. Usually the answer is a bad default, a missing guardrail, or a dashboard that showed the wrong thing.

Concretely, I'd propose three changes. Write the timeline in terms of what was known at each point, not what we know now. Ban "should have" from the document. And assign every action item to a system change, not to a person promising to be more careful.

I'll facilitate the first two if people want a model to work from. Happy to be argued out of any of it.
