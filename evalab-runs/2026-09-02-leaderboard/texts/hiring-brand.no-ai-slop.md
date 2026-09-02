## How our engineers work

We deploy about forty times a week. A fair number of those deploys come from people in their first month, because the path from branch to production is one review and a green pipeline. We would rather fix a small mistake on Tuesday than argue about a large one for a quarter.

Every service has one named owner, and that owner carries the pager. If you build it, it wakes you up at 3am when it breaks. That arrangement has done more for our timeout and retry hygiene than any style guide we ever wrote. On-call is one week in six, and the week after a rough rotation is yours to spend on whatever has been annoying you.

We have no architecture review board. A design doc runs two pages, collects comments for three days, and then the person writing the code decides. If two teams disagree, they get in a room. If they still disagree, the CTO breaks the tie that week, not next quarter.

Code review is a conversation between two people who will both maintain the thing. We ask questions in review, and we approve with open questions when the change is reversible.

Most of our engineers work remotely across seven time zones, so we write more than we talk. Decisions live in the repo, not in someone's memory of a call.

We pay for the good laptop, the second monitor, and the conference you actually want to attend. Ask your manager; the answer is usually yes.
