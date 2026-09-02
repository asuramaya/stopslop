Platform Engineering Charter

Six of us formed this team on September 1, 2026. Before that, four service teams each maintained a separate CI pipeline and a separate secret-rotation cron, and they paid for that twice: once to build it, again to patch it.

We own the path from a developer's laptop to production. That covers the build system and the deploy tooling underneath it.

Our customers are the engineers who ship product, and they can leave. If a team routes around our tooling, we go ask them what broke before we ask them to come back.

We publish paved roads and let teams opt in. You can run your own database. We will not carry the pager for it at 3am, and we say so before you launch rather than during your first outage.

We hold ourselves to two promises. We answer a request within one business day, even when the answer is no. And we ship a deprecation with a migration script and a calendar date, so you learn about a removal from us and not from a stack trace.

Marcus reviews the roadmap with team leads at the start of each quarter. Anyone can file against us in #platform-requests, and Priya triages that channel each morning.

We measure ourselves by two numbers: the median time from commit to production, and the hours engineers outside this team spend on infrastructure work. Both should fall. If they hold flat for two quarters, we got this charter wrong and we rewrite it.
