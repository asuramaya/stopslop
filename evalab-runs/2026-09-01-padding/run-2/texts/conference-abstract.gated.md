**We Split the Monolith. Here's the Part Nobody Warned Us About.**

Two years ago our Rails app was 400,000 lines and one deploy button. Today it's eleven services. This talk is about the eighteen months in between, including the six we wasted.

I'll start with the decision we got right: we didn't decompose by noun. Carving out a "User Service" and an "Order Service" because the domain diagram had those boxes gave us four services that couldn't answer a request without each other, and a p99 that tripled. We deleted two of them. What worked was cutting along the seams where teams already argued — billing, search, ingest — and leaving the mushy middle alone. Six of the original modules are still in the monolith. They're fine there.

Then the part nobody warned us about: the implicit guarantees. A single database transaction had been doing our consistency work for free. Once it was gone we wrote that work by hand, in every service, and got it wrong three times before we shipped an outbox table.

You'll leave with the seam test we use now, our rollback pattern for a half-migrated service, and a short list of things worth keeping in the monolith permanently.

*(~205 words)*
