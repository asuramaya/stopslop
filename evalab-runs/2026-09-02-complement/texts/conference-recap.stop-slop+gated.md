Five of us flew to Portland for RenderCon. We split the track list on the plane and agreed to skip any talk with "AI" in the title.

Priya sat through the incident-review session from the Shopify infra team. Their on-call engineer writes the timeline before anyone assigns blame, and that timeline lives in the same repo as the code. Ours had sat in Notion since 2023. Priya moved the last four postmortems into the repo on Thursday night.

Marcus spent both days in the hallway. He found four teams running the same Postgres upgrade we have been putting off since March, and three of them hit the same lock timeout on large tables. One team had written a script for it. Marcus asked, and the engineer sent it over before the closing keynote.

The vendor floor gave us badge scans and lukewarm coffee. We learned nothing there we can use.

The migration talk changed how I think about our deploy order. The speaker, an engineer at Faire, ships the column first and the code a week after. We ship both at once and then argue about rollbacks at 2am. I want to try her order on the billing service in October.

Two changes start this week. Postmortems live in the repo now, and Dana owns the Postgres upgrade with the script Marcus brought back.

Registration for next year opens in November. I would send two people and tell them to work the hallway, sit in on the infra track, and stay off the vendor floor.
