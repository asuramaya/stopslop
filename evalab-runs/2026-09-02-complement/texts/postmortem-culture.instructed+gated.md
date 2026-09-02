Subject: incident review should record causes, not culprits

Last quarter's checkout outage ended the way our incidents usually end. Someone's name circulated, there was a quiet conversation, and a fix landed two days later. What we never got was the sequence of events. I asked four people what happened and got four partial stories, because reconstructing the timeline honestly would have meant someone volunteering that they skipped the staging check.

That is the cost of tying incident review to individual fault. People give you the version of events that protects them, and the version that protects them is not the one that tells you why the deploy tooling made skipping staging the path of least resistance in the first place.

A blameless postmortem changes exactly one thing about how we write these up. The document records what each person knew at the time and why their action was reasonable given that information. If an engineer pushed a bad config, the question is what the config UI showed them, not why they weren't more careful. Careful is not a control. Guardrails are.

Concretely, I want to try this for the next three incidents above Sev-2:

1. A written timeline within 48 hours, authored by whoever was on call.
2. No individual names in the document; use roles.
3. Action items that change a system, with an owner and a date. "Be more careful" is not an action item.
4. Distribute the write-up to all of engineering, not just the team involved.

We do not have to invent a format. Google, Etsy, and Honeycomb have all published theirs, and I have drafted a template from the Google SRE workbook chapter on postmortem culture. I will run the next one myself so the first pass costs nobody else time. Pair with me on it if you want to see how it goes.
