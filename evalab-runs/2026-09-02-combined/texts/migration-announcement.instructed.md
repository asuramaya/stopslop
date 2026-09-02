We're moving Northwind Analytics to a new platform on March 3, 2026.

The current system has been running on infrastructure we first stood up in 2019, and it has reached the point where adding anything new means working around it rather than with it. The replacement runs on a rebuilt data pipeline, which is what lets us fix the two things you've told us about most often: report generation that slows down past 50 million rows, and the six-hour lag on dashboard refreshes. On the new platform, refreshes complete in under ten minutes.

What this means for you, in order of when it happens:

1. Between now and February 20, nothing changes. Keep working as you do today.
2. On February 21 we open the new platform in parallel. Both systems run at once, and your account works in either. Use the parallel window to check that your saved reports and scheduled exports came across correctly.
3. On March 3 the old platform goes read-only. You can still export historical data from it until June 30, after which it is retired.

Your data migrates automatically. Saved reports, scheduled exports, user permissions and API keys all carry over. Two things do not: custom SQL views written against the legacy schema, and webhooks pointing at the v1 endpoint. If either applies to your account, your account manager will contact you this week with the specific list and a rewrite.

Pricing does not change.

The migration guide is at docs.northwind.com/migration. If something in your workflow isn't covered there, reply to this email and we'll answer within one business day.
