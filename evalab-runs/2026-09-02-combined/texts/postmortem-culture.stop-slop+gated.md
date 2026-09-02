Why our incident reviews should stop naming people

The checkout outage in July lasted 40 minutes. Three engineers spent the following week rehearsing answers for the review meeting, and none of us wrote down why the old retry setting passed code review in the first place.

I want to run the next review without asking who did it.

A blameless postmortem asks why the wrong move looked right at the time. Sarah pushed that config because staging reports a green deploy for a setting that falls over under production load. She read the dashboard the way any of us would have. If we spend the hour deciding whether Sarah was careless, we keep the dashboard. Engineers who expect to be named hide things. They fix the symptom at 2am and skip the writeup, and six months later the same failure lands on a teammate who starts from zero. We did this twice with the payment queue, and both times the second engineer rebuilt the timeline from Slack scrollback.

Blameless does not mean consequence-free. If someone ships without tests on purpose, that's a conversation with their manager, and it happens outside the postmortem. The postmortem produces a list of changes to our systems, with owners and dates against each one.

My proposal. For any incident over 15 minutes of customer impact, we write the timeline within two business days and name systems rather than people in the document. Someone outside the responding team runs the meeting and owns the follow-ups.

Try it on the next incident. If our writeups get thinner by December, I'll drop it and we go back to the current format.
