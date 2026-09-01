**On writing up incidents without picking someone to blame**

We had four incidents last quarter. In each one, somebody in the room already knew what had gone wrong, and in each one the conversation ended at that person. The deploy that skipped staging. The migration run against prod. The 2am alert someone silenced. We fix the person, we move on, and six weeks later somebody else does something adjacent and we all act surprised.

I want us to start running postmortems, and to run them blameless.

Blameless is a bad name for it. It isn't about being nice. It's that "Priya pushed the wrong config" is the end of an investigation, and "our deploy tool accepts a config it can't validate and shows a green check either way" is the start of one. The first sentence produces an apology. The second produces a ticket.

There's a practical argument too. People who expect to be named stop volunteering information. They'll tell you what happened, not what they were thinking while it happened, and the second thing is where the fixes live. We've already seen this. [Both of last year's late-surfacing incidents] were delayed for social reasons, not technical ones.

What I'm asking for is small. A doc within 48 hours of any Sev1 or Sev2, written by whoever was closest to it. Timeline, contributing factors, action items with owners. Roles instead of names in the causes section. One reviewer who wasn't on the incident.

If it hasn't earned its keep in a quarter, we drop it.

The bracketed line is a placeholder — swap in the two incidents your readers will recognize, since the argument lands much harder with real ones.
