We should run postmortems without naming a culprit

Last month's checkout outage got written up, and the write-up spent three paragraphs on who deployed the config change and one paragraph on why a bad config could reach production in the first place. We fixed the person. We did not fix the deploy path.

That is the pattern I want us to break. When a review is looking for someone to hold responsible, everyone in the room has an incentive to leave things out. The engineer who noticed the graphs looked wrong forty minutes before the page won't mention it, because mentioning it invites a question about why they didn't escalate. So we lose the forty minutes, and the next outage costs us the same forty minutes again.

A blameless postmortem is not an amnesty for carelessness. It is a rule about where the review points: at the conditions that made the mistake easy and the recovery slow. The person who typed the command is treated as a sensor, not a suspect. They saw the system in a state nobody else did, and we want that description in full.

Concretely, I'm proposing three changes. First, the incident doc drops individual names and uses roles. Second, the facilitator is someone with no ownership of the affected service. Third, every action item names a system change, not a promise to be more careful.

I'd like to try this on the next Sev1 or Sev2 and compare the action items to our last five. If the output looks the same, we drop it.
