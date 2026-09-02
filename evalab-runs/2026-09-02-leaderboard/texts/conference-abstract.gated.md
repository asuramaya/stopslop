**We Broke Up the Monolith. Twice.**

Everyone tells you to split the monolith. Nobody tells you which seam to cut first, or what to do when the second service turns out to need the first one's database.

Over three years we extracted eleven services from a 400,000-line Rails app serving 12 million requests a day. Four we later put back.

I'll walk through the decisions that held up and the ones that didn't. Why we started with billing instead of the obvious candidate. How a shared `users` table quietly became a distributed transaction problem, and the two months we spent unpicking it. What our on-call load did in year one (it doubled) and in year two (it stayed there until we fixed tracing).

You'll leave with a way to score candidate seams before you cut, a short list of the failure modes that only show up after the third service, and an honest accounting of what microservices cost us in exchange for the deploy independence we were after.

If you're being handed this migration and you're not sure it's a good idea, come anyway. Some of it wasn't.

*(207 words — swap in your real stack, request volume, and service count; the specifics are what makes an abstract get picked.)*
