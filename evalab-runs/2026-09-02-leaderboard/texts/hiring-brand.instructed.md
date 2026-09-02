## How we work

We are a team of eleven engineers, and everyone writes code — including the two people who manage others. The codebase is a single repository. You will touch parts of it you did not write, and someone else will touch what you wrote last month. We think that is healthy.

Code review is the main way we teach each other. Median time from PR open to first review comment is under four hours, and we hold that number deliberately: a review that arrives two days late is a review of code you have already stopped thinking about. Reviewers are expected to explain reasoning, not just flag lines. If you disagree with a review, say so in the thread; we would rather argue in writing than defer quietly and ship something nobody believes in.

We deploy to production about thirty times a week. Nothing goes out behind a change-advisory meeting. What we ask instead is that you can roll it back, that it is behind a flag if the blast radius is wide, and that you are around for an hour afterward to watch it.

On-call rotates weekly across the whole engineering team, and the person who was paged writes the postmortem. Postmortems name systems and decisions, never individuals.

Two things we are honest about. The build takes eleven minutes and we have not fixed it; it is on the roadmap and has been for a while. And we work asynchronously across five time zones, which means some decisions take a day longer than they would in one room. We accept that trade because it lets us hire the people we want rather than the people near an office.
