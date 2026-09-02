**Take the names out of our incident reviews**

Last month the checkout queue backed up for forty minutes. Priya wrote the review. She gave two paragraphs to the deploy she pushed and one clause to the alert that fired eleven minutes late. I read the document twice before I registered the alert at all.

That ratio is the cost of our current format. When an engineer expects the review to land on her record, she writes a defense, and a defense buries the parts we can fix.

I want us to run incident reviews without assigning fault. Names stay in the timeline, since we need to know who saw which dashboard at 14:12. Fault leaves the conclusions. We answer how a deploy reached production with no one catching the missing migration, and we drop the question of who typed the command.

Two things change. Engineers stop trimming their timelines before they submit them, so we get a record we can trust. The reviews also start pointing at our tooling, where our repeat incidents live. Priya's deploy was a symptom of a staging environment that has drifted from production since March. We have known that for six months and it sits unassigned, because our reviews end at the person who pushed.

I am not asking us to drop accountability. A team still owns its service, and a pattern of failures still calls for a hard conversation with a manager. I am asking us to hold that conversation somewhere other than the document we write to learn from an outage.

I will run the next review this way and share the format after.
