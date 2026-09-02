## Vision

By the end of 2028, a team at this company should be able to ship a new service without talking to us.

That is the whole aim. Today the median new service takes eleven weeks from first commit to production traffic, and roughly seven of those weeks are spent on work no product team should own: wiring auth, provisioning a database, getting into the deploy pipeline, arguing with the alerting config. Eight of our fourteen product teams have written their own version of the same retry-and-backoff wrapper. We know because we counted them in March.

We want that eleven weeks to be under two, and we want the path to be boring enough that nobody writes a design doc to walk it.

Getting there means treating the platform as a product with users who can leave. Internal tools survive on mandate rather than merit, and mandate hides the parts that don't work. So we will measure adoption, not compliance: if three teams route around the deploy pipeline, that is our defect, not theirs.

Two years is the horizon because the first year mostly repays debt. Consolidating the four deployment paths into one, retiring the 2021 service mesh, and moving secrets off the filesystem produce very little visible value on their own. The compounding starts in year two, once new services inherit the defaults instead of rebuilding them.

The cost is real. This is roughly six engineers held out of feature work for eight quarters. We think it is the right trade, and section 4 lays out the numbers behind that judgment.
