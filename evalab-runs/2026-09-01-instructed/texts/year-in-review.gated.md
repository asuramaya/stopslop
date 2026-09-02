## The year we stopped rewriting the same service

Twelve months ago we had four services that all did roughly the same thing to a customer record, and none of them agreed on what a customer was. Picking one was the year's real work.

We put the consolidation out in March, and it hurt. Two rollbacks, one late night that turned into a morning, and a week where the on-call rotation was basically one person and a lot of coffee. But p99 on the record-read path went from 840 ms to 210 ms, and we deleted about 30,000 lines. The quieter win was the test suite. It ran in 41 minutes in January. It runs in under 7 now, mostly because we killed the shared fixture database and stopped pretending integration tests were unit tests. Nobody blogs about that kind of thing, and it changed our days more than the March launch did.

We got two things wrong, and both were about telling people late. We underestimated the migration by a full quarter, and we told the support team about the schema change three days before it landed instead of three weeks. That one is on us, and we've since put a standing item on the Thursday sync for it.

Next year is less dramatic. Finish the auth cutover, get the last two teams off the old client library, keep the test suite under ten minutes as we add to it.

Thanks for the patience during March. And to whoever fixed the flaky S3 mock at 2am without telling anyone, we know it was you.
