We're moving to a new platform next quarter.

Starting in Q4, we're migrating the service to a new infrastructure platform. The current environment has reached its limits: response times climb during peak hours, and adding capacity gives diminishing returns. The new platform runs on infrastructure sized for where we are now, not where we were three years ago, and it removes the bottlenecks behind our recent slowdowns.

For most customers, the move requires no action. Your account, data, and integrations carry over automatically. We will email you before your specific migration window and confirm once it's complete.

A few things change. API endpoints keep their current paths, but authentication tokens issued before the cutover expire 30 days after your migration date. Generate new tokens through the dashboard once you're moved; the migration email includes direct instructions. Scheduled exports and webhooks pause for up to 15 minutes during your migration window while data transfers, and anything queued during that window runs automatically afterward.

If you're on a legacy plan tied to the old infrastructure's pricing model, your rate stays the same for at least 12 months after migration. We will reach out separately if that changes.

We're staggering migrations by account size over several weeks to keep support responsive if issues come up. If you depend on this service for time-sensitive workflows, contact your account team now to request a specific window or a dry run beforehand.

Full technical details, including the new API documentation and a rollback plan for the migration period, are on the status page. Questions go to support@[company].com.
