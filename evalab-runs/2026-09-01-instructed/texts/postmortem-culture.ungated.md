**Let's stop asking who broke it**

Three weeks ago the checkout queue backed up for 40 minutes. The writeup named an engineer in the second paragraph. That engineer has not filed an incident report since.

That's the whole argument, but I'll spell it out.

When a postmortem can end with a person's name, everyone in the room learns the same lesson: be less visible during an incident. Don't page early. Don't admit you ran the migration. Wait to see if it resolves itself. Those instincts are individually rational and collectively expensive — they add minutes to every detection window we have.

Blameless doesn't mean consequence-free, and it isn't a politeness rule. It's a claim about causation. If a single misplaced command can take down checkout, the interesting fact is the missing confirmation prompt, not the person who typed it. Someone else will type it in March. We can fix the prompt. We cannot fix "be more careful."

What I'm proposing, concretely:

- Postmortems describe systems and timelines. No names, only roles.
- The person closest to the failure writes it, and is thanked in the channel for doing so.
- Every one ends with action items that have owners and dates, or it isn't done.
- Reviews are open to anyone. Nobody's manager gets a copy as evidence.

We already do the hard technical part. We reconstruct timelines well and our monitoring is decent. What we don't have is a room where an engineer can say "I didn't understand what that flag did" without it following them into a review cycle.

Let's build that room first.
