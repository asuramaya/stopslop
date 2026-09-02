Security is not the security team's job

We have four people on the security team and roughly 180 engineers shipping code. Do the arithmetic and the current model falls apart. Every design doc that waits three weeks for a review, every finding that lands after the feature is already in production — that is the queue, not the team's competence.

So we are changing where the work sits.

Starting this sprint, threat modeling moves into the design phase and belongs to whoever writes the design doc. There is a one-page template in the handbook: what data does this touch, who can reach it, what happens if the auth check is wrong. Fifteen minutes of thinking at the right moment beats a pentest finding six months later. The security team reviews the threat model, they no longer write it.

The second change is that every team names a security champion. This is not a title or extra headcount. It is one engineer per team who gets two hours a month of training from us, joins the monthly incident review, and is the person their team asks before escalating. We are covering the training time out of the security budget, so it does not come out of your sprint.

Third, we are publishing the vulnerability backlog per team instead of one company-wide pile. You will see your own numbers, aging included.

None of this means you are on your own. Ping #security-help for anything, at any hour of the sprint, at any level of "this is probably nothing." The nothings are usually where we learn the most.
