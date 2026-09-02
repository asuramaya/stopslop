Meridian Freight — from Thursday-night releases to 40 deploys a week

Meridian Freight runs load-matching software for about 900 regional carriers. Until last spring, shipping code meant a Thursday night. Two engineers stayed late, ran the migrations by hand, watched dashboards until midnight, and told everyone else not to merge until the smoke tests came back green. Releases went out every two or three weeks. Bug fixes waited their turn behind them.

"The release wasn't hard, exactly," says Dana Okonjo, who leads platform engineering. "It was just big. By the time we pushed, we were pushing six weeks of guesses about what customers wanted."

They moved to [Platform] in March. The first month went to unglamorous work: splitting the test suite so it finished in 9 minutes instead of 50, and putting the database migrations behind a gate that could roll them back.

Then deploys got boring. Meridian went from roughly two releases a month to 40 a week, and the average change now reaches production 3 hours after the pull request merges — down from 11 days. Change failure rate dropped from 18% to 4%, mostly because a bad deploy now contains one commit instead of eighty.

The team hasn't grown. The difference is in who ships now. A third of last quarter's deploys came from engineers who never touched the old release runbook.

"I found out we'd shipped my feature by reading the changelog," Okonjo says. "That's the goal, honestly. Nobody should have to attend a deploy."
