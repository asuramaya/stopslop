**Proposal: Dedicate Q1 engineering capacity to debt reduction**

**To:** Engineering leadership
**From:** Hector Q.

I'm asking for one quarter — roughly 25% of team capacity, not a full stop on feature work — directed at the parts of the codebase that now cost us more than they should.

The case is arithmetic, not aesthetics. Over the last two quarters our median PR cycle time went from three days to nine. Most of that is not review latency; it's the work of threading a change through code paths that three people understand and nobody owns. Two of our last four incidents traced back to the same configuration layer. We patched both times because a real fix was too large to land inside a sprint. That layer will cause a third incident.

What the quarter buys:

- Consolidating the configuration layer behind one interface, so a change has one place to go wrong instead of six.
- Test coverage on the payment and auth paths, where we currently deploy on hope.
- Retiring the two dead service shims we still keep alive for one caller each.

What it costs: about six weeks of feature throughput, spread across the quarter. I'd rather name that number than bury it.

I'm not claiming this pays back in the quarter. It probably pays back in the two after, mostly as cycle time we stop losing and incidents we stop having. If we defer again, the same proposal returns next quarter with a larger number attached, because that's how this compounds.

Happy to walk through the incident data and the cycle-time breakdown before you decide.
