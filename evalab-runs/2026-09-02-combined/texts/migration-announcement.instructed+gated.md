# Northwind is moving to Atlas on April 1

We are moving the Northwind scheduling service onto Atlas, our newer platform, during Q2. The cutover date is April 1, 2027. Nothing changes for you before then.

Northwind runs on a database engine whose vendor ends support in September 2027, and the API in front of it cannot handle the request volume our largest accounts now send. We looked at patching Northwind in place and concluded the work would cost more than the move and buy us about eighteen months. Atlas already carries roughly 60% of our scheduling traffic and has run at 99.95% uptime over the past year.

What you need to do:

1. Confirm your account contact by February 15 so we send migration notices to the right person.
2. If you call the Northwind API directly, review the endpoint mapping we publish on January 20. Nine endpoints change shape; the rest are identical.
3. Book a migration window from the calendar that opens February 1. Windows run in two-hour blocks, weekdays and weekends.

If you use Northwind only through the web app or the mobile client, you have nothing to do. Your data, saved schedules, and permissions move with you.

Expect one interruption on your migration day: a read-only period of up to forty minutes while we copy your data and verify it. We will confirm the exact start time three days ahead.

Northwind stays available in read-only mode until June 30, 2027, so you can pull historical reports after your move. After that date it goes offline.

Questions go to migrations@example.com. We answer within one business day.
