Ledger Sync moves to Harbor on April 14

We move Ledger Sync to Harbor, our new platform, on April 14. Your account, your history, and your integrations come with it, and you keep the same login.

We built Harbor because the old stack runs on a scheduler we wrote in 2019 that caps sync jobs at 200 an hour. Harbor handles 5,000. Customers who batch a month-end close have sat through four-hour queue drains, and those drains go away. If you have ever started a close on Friday afternoon and watched the queue crawl through the evening, that wait is what we set out to kill.

Web app users need to do nothing before April 14. If you call our API, point your client at api.harbor.ledgersync.com and swap v2 keys for v3. You can generate v3 keys today under Settings, then API. Both versions keep working until June 30, so pick your own cutover date. On the day of the move we pause syncs from 02:00 to 04:00 UTC. Anything you queue in that window runs when we reopen, and none of it drops.

Once you are on Harbor, your audit log holds 24 months of events instead of 6. Webhooks retry for a full hour before we give up on them. The CSV exporter no longer stops at 50 MB, so the month-end pulls that used to arrive truncated now come through whole, and you can stop splitting them by ledger.

Two things retire. The legacy SOAP endpoint shuts off on April 14, and we have no replacement for it; talk to us if you still depend on it. Custom report templates need a rebuild, which takes one click under Reports, then Templates. Run it whenever you like before the move.

Email support@ledgersync.com with your account ID and we reply the same business day.

Priya and Marcus also hold open office hours every Thursday at 11:00 ET through April, and you can drop in with questions about your own setup.
