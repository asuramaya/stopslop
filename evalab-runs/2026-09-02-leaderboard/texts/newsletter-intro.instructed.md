Technical debt is the thing everyone agrees to deal with next quarter. This month we stopped agreeing and started counting.

The trigger was the checkout service. A one-line config change took four days, most of it spent tracing why three separate modules each held their own copy of the tax table. Nobody wrote that duplication on purpose. It accumulated across two migrations and one deadline, and by the time it mattered, the people who could explain it had moved to other teams.

So we did an inventory. Every service owner listed the five places in their code they dread touching, with a rough estimate of how much time each one costs per month. The list came back at 312 hours a month across eleven teams — about two full engineers, spent entirely on friction. That number changed the conversation. Debt stops being a vague complaint once it has a payroll cost attached.

Inside this issue: how the payments team paid down their ORM layer without a rewrite, why we killed the "cleanup sprint" idea after trying it twice, and a short piece from Marisol on the debt we chose to keep and why that was correct.

None of this is finished. It is just measured, which is further than we were in July.
