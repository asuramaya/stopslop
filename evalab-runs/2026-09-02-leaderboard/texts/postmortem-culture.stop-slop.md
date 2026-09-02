Subject: our next postmortem, without a culprit

Last month checkout was down for forty minutes. In the review, we spent the first twenty minutes establishing that Marco pushed the config change, and four minutes on the fact that staging has never mirrored production's connection pool limits. We got that ratio backwards.

I want to run the next incident review blameless. One rule: the writeup describes what happened and assigns fault to no person. Marco pushed the change, and we say so, because the timeline needs it. We skip the part where we ask why he was careless, and we skip the line recommending extra review on his commits.

My reason is selfish. Engineers who expect to be named start hiding things. They round "I wasn't sure the migration was safe" down to "the migration ran." They wait to report a strange graph until they can explain it. Those delays cost us minutes in the middle of an outage, and our customers pay for the minutes.

People worry this removes accountability. It moves it. We hold the team accountable for shipping the fixes the writeup names, each with an owner and a date, and I will chase those in the weekly. We stop putting one person's judgment on trial in a document forty engineers read.

Etsy published its template a decade ago and I've adapted it into two pages in the wiki. The facilitator role rotates, and it isn't the incident commander.

Let's try this on the next Sev-1, then compare the action items against our last three reviews. If the writeups get vaguer and the fixes get weaker, we go back to what we do now.
