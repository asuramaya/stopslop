**Subject: [Service] moves to [New Platform] starting [date]**

We're moving [Service] to [New Platform] next quarter. The migration runs from [start date] to [end date].

What changes:

- You'll sign in at [new URL]. Your current username and password still work.
- API traffic moves from [old endpoint] to [new endpoint]. The old endpoint keeps serving requests until [sunset date], then returns 410.
- [Feature] won't be available at launch. We expect it back by [date].

What doesn't change: your data, your pricing, your existing integrations, and your support contacts.

There's one maintenance window, on [date] from [time] to [time] [timezone]. [Service] will be read-only for about [N] hours. Scheduled jobs queued during the window run when it ends.

You don't need to do anything before [date]. If you call our API from your own code, update the endpoint any time between now and [sunset date]; we'll email a reminder at 30 days and again at 7 days.

We're moving because [old platform] caps accounts at [N] concurrent connections and hasn't shipped [capability] we've asked for since [year]. On [New Platform] we can raise that cap to [N] and start work on [specific thing customers asked for].

Full migration notes, including the endpoint mapping and a test environment you can point at today, are at [link].

Questions go to [email] or your account manager. If the timing breaks something on your end, tell us before [date] and we'll work out a separate window with you.
