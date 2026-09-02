Your checkout service starts returning 500s at 2:14 a.m. The dashboard shows CPU at 12%, memory flat, error rate climbing. On-call gets paged and spends forty minutes SSHing into boxes and grepping logs before finding it: a connection pool exhausted by a retry loop that shipped Tuesday.

Those forty minutes are what monitoring without observability costs. Monitoring answers questions you wrote down in advance, in the form of dashboards and alert thresholds. It tells you something broke. Observability answers the questions you didn't think to ask, because the data carries enough detail to slice after the fact: by customer, by region, by build SHA, by the one feature flag that was on for 3% of traffic.

The difference shows up in how teams behave. A team with dashboards asks "is it down?" A team with traces asks "which of the eleven services in this request path added 800ms, and for whom?" The first question ends in a war room; the second ends in a pull request.

The gap widens as systems get smaller and more numerous. A monolith with one database has maybe a dozen failure modes an experienced engineer can hold in their head. Forty services talking over a network have failure modes nobody has enumerated, including the ones that surface only under load, at a specific hour, for users in one region.

Alerts catch the failures someone imagined ahead of time. Everything else you have to ask about afterward, and you can only ask if each request carried enough context to answer.
