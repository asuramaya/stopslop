**Subject: We're moving Ledgerline to a new platform in Q1**

Starting January 12, your Ledgerline account lives on a different system. Same login, same data, new house.

Why bother? The old stack ran on infrastructure we've been patching since 2019, and every patch made the next one harder. Export jobs that used to take four seconds were taking forty. We got tired of apologizing for it.

What actually changes for you: report exports come back as .xlsx by default instead of .csv, and the API base URL shifts to api.ledgerline.io/v3. Old endpoints keep answering until June 30, so nobody has to scramble. Your saved views, your team permissions, your billing history all come across untouched. We tested the migration against a copy of production eleven times before committing to a date.

There's a two-hour window on January 12, from 02:00 to 04:00 UTC, when the app will be read only. You can look at things. You can't change them.

Honestly, the part I'd flag: if you've built anything against the v2 webhook payload, the timestamp field changes from Unix seconds to ISO 8601. That one bit us internally and it'll bite some of you too. Docs for the new shape are up now at docs.ledgerline.io/webhooks, and Priya on our support team has been answering migration questions all week if you want a human.

We'll send a reminder eight days out and another the morning of. After that, no more emails about this, promise.

If something breaks, write to support@ledgerline.io and put MIGRATION in the subject. Those go to the top of the queue through the end of February.
