We are moving Ledgerline to Atlas on 14 January.

Atlas runs the same billing engine you use today, on hardware our team controls end to end. Your invoices and payment history move with you, and your login stays the same. Your price and your contract terms stay where they are, and nobody on our side touches your plan during the move. Expect one interruption. On 14 January, between 02:00 and 06:00 UTC, our engineers take the service offline while they cut the database over. You cannot log in or submit payments during those four hours. Anything you schedule inside that window runs at 06:15.

Two things change after the cutover. The API base URL becomes api.atlas.ledgerline.com, and your current keys stop working on 1 March. You can generate new keys from Settings > API from 14 January onward. Both sets answer requests until 1 March, so you can move one integration at a time instead of rewriting everything in a weekend. We will send a checklist for API customers on 8 January.

We ran the migration twice against a copy of production data. The second run finished in 71 minutes with no record mismatches, which is where the four-hour window comes from.

If the cutover runs past 06:00, we roll back to the current platform and write to you the same morning with a new date. Priya Raman leads the migration team. Write to her at priya.raman@ledgerline.com with questions about your own integrations, and she or one of her engineers will answer within a business day. We will send a short confirmation once your account lands on Atlas.
