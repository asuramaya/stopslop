## Security isn't the security team's job

Six people can't watch four hundred repositories. That's the whole argument, and everything below is just detail.

Right now, the pattern goes like this: someone ships a feature, it goes to security review late, security finds a problem, and the fix costs three times what it would have cost in design. Nobody is happy in that sequence. Not the engineer who has to unpick a week of work, not the reviewer who becomes the person who says no, and not the customer waiting on a date that keeps moving.

So we're changing where the work happens, not who does it.

Three things, starting this quarter:

**Threat modeling at design, not review.** Half an hour with a whiteboard when the design doc is still soft. What are we storing, who can reach it, what happens if this gets it wrong. Security will sit in on the first few until the habit sticks.

**Every team names a security champion.** Not a second job, and not an expert. A person who knows where the checklist lives and who to ask. They get a monthly session with the security team and a direct line when something looks off.

**Reporting stays free.** If you find something, or think you might have caused something, say so. No blame, no incident review with your name at the top. We would rather hear about ten false alarms than miss the one that matters.

The security team isn't going anywhere. They're moving from gatekeeper to the people who make it easier for the rest of us to get this right the first time.
