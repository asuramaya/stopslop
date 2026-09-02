## Engineering

You ship code in your first week. Someone on your team pairs with you on the first change, and a reviewer picks it up that afternoon.

We keep teams at five or six engineers, and each team owns its services from the design doc through the pager. The engineer who writes the migration answers the alert at 2am, which shapes how we write migrations.

Code review is a conversation. Reviewers ask questions and offer alternatives, and two approvals move a change to main. If your review sits untouched for a day, ping the reviewer in the team channel. We treat a stalled review as a problem for the team to fix, not something you should wait out.

We write things down. Engineers draft a design doc before a large change and publish a review after an outage. You can find out why we chose Postgres over DynamoDB in 2023 in about four minutes, without digging through Slack archives.

We disagree in the open. An engineer six weeks in can push back on the tech lead's proposal during design review, and the lead either changes the design or explains the constraint they missed. Both outcomes count as a good meeting.

On-call rotates weekly. If the pager wakes you at night, you take the next morning off, and the team spends part of the following week fixing the alert that woke you.

Two afternoons a month, you work on whatever you want in the codebase. Some of that work becomes our tooling. Some of it stays a branch nobody merges, and we're fine with that.
