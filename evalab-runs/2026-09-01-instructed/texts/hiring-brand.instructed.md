# How we work

We're about forty engineers, and roughly half of us have shipped code that broke something in production. That's not a confession, it's arithmetic on a team that deploys around eleven times a day.

Reviews are the center of gravity here. Every change gets read by someone who didn't write it, and reviewers are expected to say "I don't understand this" out loud rather than approving on faith. A review that takes two days is a signal we've built something too tangled to explain, and we treat it that way.

We write things down. Design docs run two to four pages, circulate for a week, and record the options we rejected along with why. When someone asks a year later why the billing service talks to Postgres instead of the event bus, the answer is in a document with a name attached to it.

On-call is one week in six, and the engineer who carries the pager is the one who wrote the service. Pages that fire more than twice without a fix become sprint work, not tribal knowledge.

You'll own something within your first month. New engineers ship to production in their first week, usually a small fix, occasionally something larger if they push for it. Your manager writes code for at least a fifth of their time, so the person reviewing your work still remembers what the build takes.

We disagree in writing and in meetings, and we're not always graceful about it. What we do consistently: the decision gets made, the reasoning gets recorded, and nobody relitigates it in the hallway afterward.
