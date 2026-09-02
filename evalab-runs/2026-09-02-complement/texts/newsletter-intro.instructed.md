# The month we stopped calling it debt

Last quarter's incident review turned up something none of us wanted to write down: four of the seven production incidents traced back to code that at least one engineer had flagged as "we should clean this up" more than a year earlier. Nobody was surprised. That's the part worth sitting with.

We've been using the word "debt" loosely, and the metaphor has started doing work it can't support. Debt implies you chose the loan, you know the balance, and the interest is predictable. Most of what we're carrying is none of those things. It's code someone wrote correctly in 2023 against assumptions that quietly stopped holding in 2025.

So this issue is less about paying anything down and more about seeing it clearly. Priya writes about the payments retry logic, and why the fix took three weeks instead of the estimated two days. Marcus has numbers from the dependency audit — 41% of our direct dependencies haven't been updated in over 18 months, and he explains which of those actually matter. There's a piece on the deprecation process we tried in Q2, including the part that failed.

No grand cleanup initiative is coming. What we can do is stop pretending the mess is temporary and start budgeting for it like the permanent line item it is.
