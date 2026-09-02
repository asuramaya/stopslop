Subject: Ledger Sync moves to the new platform in Q1

We move Ledger Sync onto our new platform between January 6 and March 20. You keep the same login and the same billing date.

We built the new platform to fix the two complaints you sent us most often. Exports timed out on files over 2 GB, and a new webhook took four hours to go live. On the new platform, a 10 GB export finishes in about nine minutes and a webhook starts firing inside a minute.

We move accounts in batches. You get one email fourteen days before your batch date and a second email the morning of the move. We take your service offline for roughly twenty minutes during the switch, and we schedule every batch between 02:00 and 04:00 in your account's time zone.

Two items need your attention before that date.

If you call our API, point your client at api2.ledgersync.com. We shut off the old hostname on April 15.

If you pull the v1 CSV export, download the new column layout from ledgersync.com/migration and update the script that reads it. We added two columns and renamed `txn_ref` to `transaction_id`.

We keep the old platform running until April 15. If something breaks after your move, our support team can put you back on the old platform within an hour while we sort it out.

The migration team answers migration@ledgersync.com and replies within one business day. Send us your account ID and we will tell you which batch you sit in.
