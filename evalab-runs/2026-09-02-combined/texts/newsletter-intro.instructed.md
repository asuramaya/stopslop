# Technical debt

Last quarter we spent 31% of engineering hours on work that existed only because of decisions we made two and three years ago. That number came out of the sprint retro tagging exercise Priya ran in July, and it is the reason this issue exists.

Technical debt is a bad metaphor that we keep using because nothing better has stuck. Debt implies you chose to borrow. Most of what slows us down was never a choice — it was a reasonable call made with less information, or a workaround that outlived the outage it was written for. The auth middleware nobody wants to touch started as a two-day patch in 2023.

Inside, four pieces. Marcus writes up the payments service migration, including the part where we shipped the strangler façade and then left it half-strangled for eight months. Dana makes the case that our test suite is itself a form of debt: 40 minutes to run, and engineers have started pushing without it. Wei covers what we learned from setting a fixed 20% budget for cleanup work, which did not go how anyone expected. And there's a short piece from the platform team on deleting things.

None of this ends with a framework. The honest position is that we are still arguing about how to prioritize this work, and the arguments are worth reading.
