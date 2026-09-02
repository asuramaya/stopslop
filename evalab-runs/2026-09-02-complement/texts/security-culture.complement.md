**Everyone owns security here**

We have four security engineers and about three hundred people shipping code. That ratio has never worked as a review queue, and pretending otherwise is why review requests sit for nine days before anyone looks at them. So we're changing where security work happens.

Starting this sprint, three things move to the teams that own the code.

Design docs get a threat model section. Half a page: what data this touches, who could reach it, what breaks if they do. Ryan's team wrote a good one for the billing migration and it's linked in the template as an example.

Dependency changes get a second reviewer on the PR, same as schema changes already do. The tooling flags new packages automatically; you just need a human to say why we're adding it.

Secrets and access reviews happen quarterly at the team level. Your team knows which of its service accounts are stale. Security does not.

What stays with the security team: incident response, pen test coordination, the vulnerability scanner, and any question you want to hand off. Office hours are Tuesdays at 2, and the #sec-help channel has a fifteen-minute response target during work hours.

One thing worth saying plainly. If you find something you broke, or something you shipped two years ago that looks wrong now, report it. Nobody gets written up for reporting. We have shipped bad code, all of us, and the only version of this that fails is the one where people stay quiet.

Questions to me or to Dana. We'll revisit in six weeks and cut whatever isn't earning its time.
