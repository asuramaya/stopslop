## Let's stop asking who broke it

Last month checkout went down for forty minutes. In the review we spent most of an hour establishing that Priya had pushed the config change, and four minutes on the fact that the config never passed through a staging environment that could have rejected it. That ratio is the argument for changing how we run these. Priya learned to be careful. The rest of us learned to keep quiet. Nobody wrote down that a one-line config edit reaches production untested, so in six weeks someone repeats the edit and we hold the same meeting with a different name in it.

I want the next review to run under one rule: we do not name the person who typed the command. We name the system that accepted it. The writeup carries a timeline and a list of changes, each with an owner and a date.

There is a selfish reason too. An engineer who expects to be named in the review reports the incident late. She checks whether she can fix it alone first, and the outage runs an extra twenty minutes while she tries. I have done this on the billing migration in March, and I would do it again under the current setup, which is the point.

Someone will say people get sloppy once we stop holding them responsible.

We still hold them responsible, for the remediation ticket with their name on it and a due date next Friday. That is a consequence. Getting scolded in a room is not. Try it on whatever breaks next, then read that writeup against the last three we filed and tell me which one you would hand to a new hire.
