I nominate the Deploy Platform team for this year's Engineering Excellence Award: Priya Raghunathan, Marco Silva, and Dan Okonkwo.

In January, a production release cost the on-call engineer ninety minutes of manual steps, and two releases per quarter ended in a rollback. Priya rewrote the pipeline so that one command builds an artifact and promotes it through staging. Marco threw out the hand-maintained environment YAML and generated it from the service manifests, which killed the config drift that used to page people at 2am. Dan built the rollback path, then made the team rehearse it against a copy of production every month. Our last four incidents closed in under six minutes.

A release now takes eleven minutes. The Payments team ships on Fridays again, something their director had forbidden since the 2024 outage.

The three of them carried their regular roadmap work through all of this. They also wrote the migration guide, which let eleven service owners move over without filing a single ticket.

Last week Sarah Kim told me her team deleted their deploy runbook. They read it, realized none of the steps applied anymore, and closed the doc. That is the strongest endorsement I can offer on their behalf.
