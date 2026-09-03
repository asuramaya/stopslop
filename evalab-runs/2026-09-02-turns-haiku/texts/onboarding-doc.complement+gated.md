Welcome to the payments team. You'll be working on the systems that process and reconcile transactions—the money moving through our platform.

Your first week priorities:

Read `docs/payments-architecture.md`. It covers transaction flow, database schemas, and how services connect. Set up your local environment using the README in the `payments-service` repo. Run integration tests to verify everything works. Attend standup each morning at 9am to meet the team and learn what's in progress.

Check our Grafana dashboards at `monitoring/payments-dashboards`. They show transaction volume, latency, and error rates. We watch these closely because payment failures directly harm customers.

Your first task will be small—a bug fix or minor feature. Your mentor will pair with you on it to show our testing practices and code review process.

Precision, safety, and clarity matter most in this work. We have extensive tests because mistakes cost money. Code reviews are thorough. Comments explain tricky logic. This is slower than some engineering, but it's the right pace for this domain. The team Discord channel is `#payments-eng`. Use it for questions. Your first real contribution matters. We're glad you're here.

Who to ask for what:

Ask your mentor for code review questions and onboarding blockers. Ask the tech lead for architecture decisions and schema changes. Ask the on-call engineer for production incidents and urgent bugs. Ask the database team for query optimization and schema reviews. Ask the security team before handling sensitive payment data in new ways. The #payments-eng Discord channel works for general questions the whole team can answer.

On-call rotation:

The team rotates on-call duty weekly. You won't take on-call for your first month—use that time to understand our systems and incident response. When you join the rotation, you'll carry a pager for a week and handle alerts. Expect 1–2 incidents per rotation on average. Your first on-call week, you shadow an experienced engineer.
