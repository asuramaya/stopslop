# What We Brought Back From QCon

Five of us flew out for QCon last week, and the flight home felt different than the one out. Three sessions changed how we think about the next quarter.

The first was a talk on incident review formats. The speaker walked through six months of postmortems at a mid-size fintech and showed how switching from a timeline format to a "decision tree" format cut repeat incidents by a third. We're piloting the same format on our next two postmortems.

The second was less a talk and more an argument, in the hallway, about whether feature flags belong in the database or the config file. We landed on database, mostly because two attendees from unrelated companies had both migrated away from config files after a bad deploy locked them out of their own kill switch. That's now on our backlog.

The third came from a workshop on on-call rotations. The facilitator had us map our actual paging load against team size, and the math was worse than any of us expected: our busiest engineer had handled forty percent more pages than the median over the last quarter. We're rebalancing the rotation this month.

Not every session earned its slot. A panel on "AI-native engineering" spent forty minutes on vocabulary and ten on anything we could use.

The real value showed up between sessions: two vendor conversations turned into a shortlist for our logging migration, and a conversation over coffee gave us a name for a bug pattern we'd been describing badly for a year.

Next year we're sending two more people.
