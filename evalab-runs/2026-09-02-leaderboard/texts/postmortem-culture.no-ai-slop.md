Subject: Stop asking who broke it

Our incident reviews end the same way every time. The person closest to the failure walks us through what they typed, everyone nods, and the action item is some version of "be more careful." Nothing about the system changes. The next engineer who hits that path stays quiet about it, because they watched what happened to the last one.

I want our next review to name no one.

People do make mistakes. A mistake that takes down checkout for forty minutes is also a system that let one unreviewed command take down checkout for forty minutes. The second problem is the one we can fix, and we keep skipping it to argue about the first.

Four changes:

Write the timeline with roles, not names. "The on-call engineer" is enough to follow the story.

Ask what made the wrong action look right at the time. If the runbook was stale or the dashboard showed green, that's the finding.

Require every action item to be a change to a system: a guardrail, a default, an alert, a rollback path. "More training" and "more care" don't count.

Publish the write-up to the whole company. Half the value is for the team that hasn't hit that failure yet.

The cost is a couple of hours of writing per incident. What we get back is people reporting near-misses before they turn into incidents, which is the part we have no visibility into today.

I'll run the next one this way if nobody objects.
