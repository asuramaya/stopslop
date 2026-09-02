Vision

By the end of 2028, a product engineer clones a repo, runs one command, and watches a service reach staging before lunch. That same path takes eleven days and four Slack threads today.

Four of our six product teams wrote their own deploy scripts last year, their own metrics wiring, their own retry logic. Priya's team spent five weeks on a migration runner that Dan's team had shipped in March. Platform work means we write that runner once and the other teams delete their copies.

Two commitments anchor the next two years.

First, we own the boring middle. Auth, deploys, observability, and data access belong to the platform group, with SLAs and a named person on call for each. Product engineers stop reading Terraform.

Second, we measure ourselves by what product teams ship, not by what we ship. Our scorecard tracks time from first commit to production traffic, plus the number of platform tickets a team files to get unblocked. If those numbers hold flat through 2027, we chose wrong, and we say so in the quarterly review rather than waiting for someone else to notice.

This costs us. We move seven engineers off feature work in Q1, which pushes the billing rewrite back a quarter. Sarah and I agreed to that trade in August. We plan to defend it in February, when a customer escalates and someone asks why we have nobody to spare.

In September 2028 we run the same clone-and-deploy test and publish the number. Eleven days would mean we spent two years and seven engineers on nothing.
