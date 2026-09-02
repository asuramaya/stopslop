## Vision

Two years from now, a new engineer should be able to ship a service to production on their first week, and nobody should have to ask them how they did it.

That's the whole bet. Right now the answer to "how do I deploy this" depends on who you ask and which team wrote the service. We have four ways to run a background job, three logging conventions, and a staging environment that four teams quietly maintain private forks of. Every product team pays a tax to work around this, and because the tax is paid in small increments — an afternoon here, a bad on-call night there — it never shows up on a roadmap as something worth fixing.

We're going to make it show up. Over the next eight quarters we want the default path to be the easy path: one deployment pipeline, one way to define a service, one place where ownership and alerting live. Teams that need to step off that path still can. They just won't have to step off it to do ordinary work.

We're not chasing an internal developer platform as a product, with a portal and a roadmap of its own. Portals are what you build when the underlying system is too confusing to use directly. We'd rather fix the confusion.

The measure we care about is time from first commit to first production deploy for a service that doesn't exist yet. Today that's roughly three weeks of mostly-waiting. We think it can be two days.

---

The specifics — four job runners, three-week onboarding, eight quarters — are placeholders. Swap in your real numbers, or tell me the actual state and I'll rewrite against it.
