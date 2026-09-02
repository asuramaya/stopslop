# How we build

You ship to production in your first week. An engineer on your team pairs with you, walks through the deploy pipeline, and stays on the call until your change is live. Setup takes two days, and after that you're writing code that customers use.

Teams here run four to six people. Each team owns its services from design doc through pager rotation, and our on-call runs one week in six. If you write it, you run it, and you get the budget to fix what wakes you at 3 a.m.

Reviewers ask questions and suggest alternatives, and they respond within a working day. We don't let a pull request sit for a week while someone assembles objections to it.

We write things down. Design docs land in a shared repo before the work starts, and anyone at the company can comment on them. Two of our engineers argued for three months about the storage layer in a doc that now runs to 40 pages. They chose Postgres, the doc explains their reasoning, and new hires read it in their second week. That argument saved us a migration we would have paid for in 2024, and it settled a question the two of them had been relitigating in every planning meeting for a year.

One week each quarter belongs to the team. Last quarter one group cut the test suite from 22 minutes to 6. Another rewrote the billing service that three people had been afraid to touch since 2019.

You'll find systems we built under a deadline and want to replace them. Bring us the argument. We fund about half of those proposals, and we tell you our reasons when we pass on yours.
