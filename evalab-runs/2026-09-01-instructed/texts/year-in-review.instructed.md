# The year in review

We shipped 41 releases this year. Two of them were good.

That's a joke, but only partly. The February auth migration took eleven weeks against a four-week estimate, and we spent most of March cleaning up after it. The retro on that one is still worth rereading if you joined after Q2: the failure wasn't technical, it was that three teams each assumed someone else owned the session-token rollover.

What actually went well: median PR review time dropped from 31 hours to under 6. Nobody made that a goal. It happened because Priya moved the review queue into the channel people already read, and because we stopped requiring two approvals on config-only changes. Small process changes, large effect.

The platform team rebuilt the CI pipeline in the summer. Build times went from 24 minutes to 9. The interesting part is what they cut rather than what they added — about 40% of the old pipeline was tests that had never once failed on a real regression.

We hired six engineers and lost two. Both departures were people who'd been here over four years, and both said in their exit interviews that on-call had gotten worse. It has. We paged someone 340 times this year across a rotation of nine people. That's the number I'd most like to change in the coming year, and it won't change by asking people to be more careful.

Next quarter's planning doc goes out Monday. Read it before the meeting.
