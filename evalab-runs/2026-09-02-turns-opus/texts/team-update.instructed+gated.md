# Engineering update — September

Checkout has moved again, October 3rd to November 14th. Different reason this time.

Last month it was the payment path touching the old schema. Fixed that. But we never checked the refund and chargeback flows, which live behind a service another team owns, and they read three columns we dropped. That team can pick it up October 20th. The alternative is a shim we'd throw away in December, two weeks of work and a second code path in billing. Not worth it, so we wait.

Dana's scoping review caught the payment path but stopped at our repo boundary. So we're adding a rule that anything crossing teams needs a named owner on the other side before we pick a date. Marcus is writing that up with her.

Priya and Jen split on-call while Marcus ramped, including the September 8th pager storm. Thank you both.

Sales and support have November 14th. I won't call it firm, I've done that twice now. It's what we believe today.
