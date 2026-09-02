**Proposal: One quarter of engineering capacity for debt reduction**
To: Leadership
From: Platform Engineering

We are asking to dedicate Q4 engineering time to paying down accumulated technical debt in the billing and notification services, at a cost of roughly one quarter of team capacity.

The case is in the numbers we already track. Over the last two quarters, 38% of engineering hours went to unplanned work: production incidents, hotfixes, and rework on features that broke adjacent code. Billing alone accounted for 21 of the 34 P1 incidents. Median time to ship a small billing change has gone from four days to eleven, because every change requires manual regression testing that our test suite cannot cover.

The work we propose is specific. Replace the three overlapping payment-state tables with a single ledger. Retire the 2019 notification queue, which has no owner and no runbook. Bring billing test coverage from 22% to 70%, focused on the refund and proration paths that generate the most incidents. Delete the two abandoned service copies still receiving traffic.

We estimate 9 engineer-weeks for the ledger migration, 4 for the queue retirement, 6 for test coverage, and 2 for cleanup. That fits inside the quarter with room for the on-call rotation.

What we give up: the merchant dashboard refresh and the second phase of the partner API slip to Q1. We keep committed customer deliverables and the SOC 2 remediation items.

What we expect in return: unplanned work below 20% of hours by end of Q1, and billing changes shipping in under a week again.

We can present the incident data in detail at your convenience.
