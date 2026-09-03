**How Meridian Freight cut release day from once a month to every afternoon**

Meridian Freight's engineering team used to ship code on the last Thursday of every month. The release took a full day. Someone ran a manual checklist while three people sat on a call, and nobody wanted to test the rollback plan. Bugs that shipped stayed live for weeks because nobody wanted to touch the pipeline again so soon.

In January, the team moved their deploy process onto Northlane, a continuous delivery platform that runs tests, staged rollouts, and rollback checks automatically on every merge to main. The first two weeks were mostly cleanup. They split a monolithic build script into stages Northlane could run independently and wrote tests for a payments module that had none.

By March, Meridian deployed eleven times a week. By June, that number climbed to over thirty. Small fixes go out within hours instead of waiting for the next release window. When a bug reaches production, the team catches it the same day, because they aren't debugging a month's worth of changes at once.

"We used to treat deploys like surgery," said Priya Nadeen, Meridian's VP of Engineering. "Now it's closer to sending an email. If something's wrong, we fix it and push again ten minutes later."

The change also affected who deploys. Under the old process, only two senior engineers were trusted to run a release. Now any engineer can merge and ship their own change, with Northlane's automated checks acting as the gate.

Meridian is extending the same pipeline to their mobile app next. That app still ships on a two-week cycle.
