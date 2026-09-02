I nominate the Release Tooling team for the Engineering Excellence award.

Last January, a production deploy cost us a four-hour Thursday window. Two engineers watched dashboards while the rest of us waited on Slack. One release in three got rolled back before Monday.

Priya and Marcus took the problem apart. They built a canary stage that routes 2% of traffic to the new build and holds it there for ten minutes. They replaced the hand-written runbook with a pipeline that fails closed on a bad health check. Before either of those, they spent six weeks on test flakiness, because engineers skip a deploy gate they don't trust.

Deploys now finish in eleven minutes. We ship Tuesday afternoons. Rollbacks dropped to one in twenty, and both rollbacks this quarter completed in under ninety seconds.

They did all of this on top of their roadmap commitments, in the gaps between other work. Nobody handed them a free quarter for tooling. They took the on-call pain personally and worked it down release by release.

Ask anyone who shipped code here before and after. Meera told me last week that she stopped scheduling her Thursday evenings around a release window. Priya and Marcus gave her those evenings back.
