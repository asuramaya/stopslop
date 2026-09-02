# Design Philosophy

We built this API so you can guess the second endpoint after learning the first. Resources are plural nouns. The verb lives in the HTTP method. Once you can list invoices, you can list refunds without opening this page again.

Errors tell you what to fix. An error body names the field, the value we received, and the constraint it broke. You will not read our source code to find out why a call failed.

We pin your version at the account level and leave it alone until you move it. Old fields stay where they are. New fields arrive as keys your parser does not recognize, and it drops them, so your integration from two years ago keeps running.

We chose boring over clever. Auth is a bearer token. Filters are query parameters. You will not learn a wire format before your first request.

We assume you call us from a cron job at 3am with nobody watching the logs. So writes take an idempotency key, reads return a cursor, and we put your remaining quota in a response header long before you exhaust it. When something breaks at that hour, you want a retry that behaves the same way twice, and we owe you that.
