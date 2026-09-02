We ran a 400,000-line Rails monolith for nine years. A deploy took 40 minutes. One bad migration in the checkout code froze the other six teams until someone reverted it, and that happened twice a month.

We cut it into 23 services over two years. I will show you what that cost.

Our first extraction failed. We picked billing because it looked self-contained on the architecture diagram. Billing shared four tables with orders, and we spent five months untangling foreign keys before the service answered a single request. The second extraction took six weeks. We picked search, which owned its data and talked to the rest of the app through one endpoint.

The difference was not team skill. We changed how we chose the next service: read the schema, count the shared tables, and refuse anything above two until you have split the data first.

I will also cover the bills nobody warned us about. Our AWS spend rose 60 percent in the first year. Our on-call rotation grew from four engineers to eleven.

Come if you maintain a monolith and your CTO has asked about microservices. You will leave with the checklist we now run before we cut anything out.
