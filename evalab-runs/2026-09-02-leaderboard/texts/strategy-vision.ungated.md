## Vision

Two years from now, a new service should reach production in a week, and that week should be boring.

Right now it takes six to eight. Most of that time goes to work no team wants to own: wiring up auth, guessing at the right Terraform module, discovering on a Thursday that the staging database was never provisioned. Every team solves these problems again, slightly differently, and every variation becomes something on-call has to learn.

The platform we want is the one that makes the default path also the fast path. A team scaffolds a service and gets deployment, observability, secrets, and a rollback story without filing a ticket or reading a wiki page written in 2023. Deviating from the default stays possible, because some teams have real reasons to, but it costs them time instead of saving it.

We are not building this to reduce headcount or to centralize decisions. We are building it because our senior engineers currently spend a large share of their attention on infrastructure archaeology, and that attention is the scarcest thing we have. Give it back to them and the product roadmap moves on its own.

Two concrete markers of success. First, a new engineer ships to production in their first week without a platform engineer sitting beside them. Second, the number of distinct ways we deploy a service drops from eleven to two.

Neither is achievable in one quarter. Both are achievable by the end of 2028 if we treat the platform as a product with users, a support burden, and a roadmap, rather than as a side project that a rotating cast maintains between features.
