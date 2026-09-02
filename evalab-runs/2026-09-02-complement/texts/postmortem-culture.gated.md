# Postmortems should stop naming a culprit

Last quarter we had four incidents that cost customers real time. In three of the write-ups, the closing line was a person's name and a promise to be more careful. None of those promises held. "Be more careful" is not a change to anything.

A blameless postmortem drops the question of who and keeps the question of how.

Rather than ask why an engineer pushed the config, we ask why the config could be pushed at 6pm with no second pair of eyes, why the rollback took eleven minutes, and why the alert fired after the customer emailed us. The case for this is practical. People who expect to be named stop telling you things. They fix the symptom quietly, they leave the awkward detail out of the timeline, and they wait to see whether anyone noticed before escalating. All three cost detection time, and we have already paid for it. The March outage ran about forty minutes longer than it had to, because the first responder spent that time convincing themselves it was happening before saying so in channel.

What I want to try, for anything at sev-2 or above:

- The write-up names systems and timelines. Actions get owners; causes don't.
- Whoever runs the review was not on call for that incident.
- The doc goes out internally within five working days, unedited for comfort.

Blame feels like accountability because it produces a visible consequence within the hour. The fix that ships is the slower one, and it is the one that holds. I'll write up the next incident this way if nobody objects.
