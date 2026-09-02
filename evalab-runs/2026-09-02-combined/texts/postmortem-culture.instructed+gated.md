## We should be writing blameless postmortems

Last quarter we had four incidents worth more than an hour of downtime each. We wrote up two of them. Both write-ups named a person in the first paragraph, and neither produced a change to a system.

That pattern isn't a coincidence. When a review is going to identify who broke it, the people closest to the failure have every reason to give the thinnest account they can defend. You get "config was pushed without review" instead of the actual story: the deploy tool has no staging step, the reviewer was on PTO, the runbook says to skip review during a freeze, and this was the third time someone read that line the same way. The last four facts are the ones you can fix. The first one just ends the conversation.

Blameless doesn't mean nobody is accountable. It means the postmortem asks what made the wrong action look reasonable at the time, and accountability lands on the team that owns the fix, with a date. John Allspaw's write-up of Etsy's practice is the version I'd copy: the person who made the change writes the timeline, and they write it knowing they won't be punished for what it contains.

Concretely, I'm proposing three things. Every SEV-1 and SEV-2 gets a written postmortem within five business days. The document uses roles, not names. Every action item has an owner and a due date, and we review the open ones at the start of each ops sync.

I'll draft the template if there's appetite for trying this on the next incident.
