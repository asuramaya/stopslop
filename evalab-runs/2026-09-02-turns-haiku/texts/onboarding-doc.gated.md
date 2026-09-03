Welcome to Payments Engineering

You're joining the team that processes transactions, manages merchant accounts, and handles the financial plumbing that keeps our platform running. We move billions in volume each month across payments, payouts, and reconciliation flows. Your first week focuses on local setup, understanding our core transaction pipeline, and getting full code access to staging environments. Trace your first transaction end-to-end by Friday to understand the full flow.

Our stack is Go (payment processing, ledger), Python (reconciliation, batch jobs), and PostgreSQL, with gRPC between services and Kafka for events. GitHub Actions runs CI/CD through staging before production. We handle real money—tests must pass. Daily reconciliation catches bugs we can't find otherwise. Monitoring alerts us to delays within seconds. Report anything that seems fragile immediately.

Start with something small—a config fix or test improvement—to learn our code review process.

Your onboarding buddy is in Discord and will introduce you tomorrow, walking you through the entire monorepo structure. The team reads #payments-eng constantly and answers questions there.

Who to Ask

For architecture and system design, start with your onboarding buddy or Maria (Tech Lead)—she holds the high-level flow diagrams. On schema and database questions, reach Jason in #payments-eng; he owns the ledger schema and knows every migration. Your manager handles staging and production access, which requires explicit sign-off. For merchant or reconciliation logic, ask whoever owns that pod—the pinned list in #payments-eng shows current owners. When debugging a live issue, contact the oncall engineer in #oncall and escalate to your manager if it's critical.

On-Call Rotation

We run a weekly on-call rotation. You'll shadow the current oncall for your first month, then join the rotation starting month two. Oncall duties are light most days—monitoring dashboards and Pagerduty alerts—but you own production incidents during your week. Critical issues (transaction failures, ledger inconsistencies) get escalated to your manager and the tech lead. The on-call runbook is in the wiki; read it before your first shift.
