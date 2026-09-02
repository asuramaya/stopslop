Six of us work on security. You are two hundred engineers. That ratio decides how much our reviews can cover, and it explains why we stopped pretending a pre-launch checklist protects anything.

Starting this month, the team that writes a service owns its threat model. You write it while you design the thing, not the week before launch. Keep it to one page covering what the service holds, who talks to it, and what an attacker gains by getting in. We will read yours and argue with you about it. We will not write it for you. Two things change in your week beyond that. Rotate your own secrets. The platform team shipped the vault integration in March, and forty of our ninety services still read credentials from environment variables somebody set in 2023. Fix yours before December.

Second, triage your own dependency alerts. When Dependabot opens a PR against your repo, you decide within a week whether to merge it or write down why you won't.

You will get things wrong. Tell us the same day, and we will help you clean it up. You will not lose a bonus over a mistake you report in the morning. Hiding one is a different matter, and it has cost people their jobs here. We keep incident response, the pen test contract, and design reviews when you ask for them.

Post in #security and you get a human inside two hours during the workday. Page us at any hour if you think you are looking at a live compromise. We would rather wake up for a false alarm than read about the real one in a customer email.
