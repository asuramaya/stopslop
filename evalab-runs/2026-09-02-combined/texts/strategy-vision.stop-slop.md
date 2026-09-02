## Vision

Two years from now, an engineer joining the payments team ships a service to production before lunch on their first day. They run one command and get a repository, a deploy pipeline, staging credentials, dashboards, and a slot in an on-call rotation. They file no ticket with us. They open no wiki page that went stale in 2024.

Today that same engineer waits nine days and collects approvals from four teams. Each product group has written its own deploy script, and we maintain six ways to roll back a bad release. In March, Kafka went down and three teams debugged the same broken consumer in parallel, since none of them could see the others' alerts.

We plan to spend the next two years replacing that duplicated work with one paved road: a single deployment path, one metrics pipeline, and a service template each team can fork and then forget about. Teams that stay on the road get upgrades at no cost to them. Teams that leave it keep their autonomy and carry the operating burden themselves.

We measure this with one number: the hours an engineer spends on work that never touches their product. It sits near eleven hours a week today. We want it under three by the end of 2028.

Platform work does not show up in a quarterly demo. You see the payoff later, when the payments team ships a feature in two weeks that used to take them a quarter, and when we stop hiring an SRE for each new product line.
