Last quarter Priya spent four days shipping a two-hour feature. The billing module she needed had six entry points, and three of them wrote to the same table with different assumptions about currency. She shipped the feature. She left the six entry points where they were, because the sprint closed on Friday.

You have done a version of this. Someone took a shortcut in 2021, you route around it, and you hand the next engineer a longer detour than the one you found.

We spent this month asking what that costs us in hours we can count. Marcus pulled deploy timings for the checkout service and found that our test suite spends eleven minutes on a mocking layer two people understand. Dana wrote up the migration she abandoned in March and what she learned about why nobody funds cleanup that has no demo.

Four pieces follow. Two are postmortems on debt we chose to carry, one is Rina's argument that the payments rewrite was a mistake, and one is a short guide to writing a debt ticket that a product manager will schedule.

None of this asks you to stop shipping. It asks you to write down the price before you agree to pay it.
