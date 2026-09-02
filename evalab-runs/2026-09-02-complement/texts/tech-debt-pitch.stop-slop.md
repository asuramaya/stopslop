To: Priya Raghunathan, Marcus Bell
From: Dana Okoye, Platform
Re: Q3 engineering time

I am asking for the platform team's Q3, four engineers for twelve weeks, to rebuild the checkout data layer and retire the 2019 job scheduler.

We shipped 11 of the 19 features we committed to in the first half. The eight that slipped all touched checkout. Ramesh spent three weeks in March adding one promo-code field because the pricing logic lives in four places and two of them disagree. Wen's team writes a migration script before each release to keep the scheduler from double-firing refund jobs. That script has failed twice since January, and Finance caught both.

Two things change if you approve this. Checkout gets one pricing module that the payments team can read in an afternoon. The scheduler goes away and takes the release-night migration ritual with it.

The cost is the Q3 roadmap. We would not ship the merchant dashboard refresh or the saved-carts work. I propose we move the dashboard to Q4 and drop saved carts until we see demand past the 40 customers who asked for it.

If we defer again, the price goes up. We told you in Q1 that checkout needed six weeks. It needs twelve now. Two of the four engineers who wrote the original scheduler have left, and Wen is the last person who can debug it.

I will report progress in the Thursday staff meeting with the count of files still importing the old pricing helper. If that number stalls for three weeks, kill the project and take the engineers back.
