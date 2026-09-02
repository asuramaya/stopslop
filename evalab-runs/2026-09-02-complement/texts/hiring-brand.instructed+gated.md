# How we work

Our engineering team is about forty people across three time zones, and we've made a deliberate choice to stay asynchronous. Most decisions happen in writing — design docs, RFCs, long pull request threads — because a written argument can be read by someone who wasn't in the room, including the person who inherits the code in two years.

We deploy to production roughly thirty times a day. New engineers ship something user-facing in their first week, usually a small fix, with a reviewer sitting close by. That's not a hazing ritual; it's the fastest way to learn where the sharp edges are.

Code review here is slow on purpose. Reviewers are expected to ask why, not just whether the tests pass, and authors are expected to answer. A review that takes two days and prevents a bad abstraction is cheaper than one that takes twenty minutes and doesn't. We cap review queues so nobody is waiting on a reviewer who has eleven other things open, and we'd rather a change sit an extra day than get waved through by someone who never had time to read it properly.

On-call rotates weekly and includes everyone who writes production code, managers included. If a service pages at 3am, the team that owns it decides what to fix, and that fix goes on the roadmap rather than into someone's spare time.

We don't have a mandate about which editor, language server, or AI tooling you use. We do have opinions about test coverage on payment paths, and we will argue with you about them.

We should be honest about the parts that are less fun. Our monolith is fifteen years old in places, migrating off it is slower than we'd like, and you'd spend real time in that code.
