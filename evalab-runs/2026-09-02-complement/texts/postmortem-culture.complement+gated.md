We should write postmortems that don't name a culprit

Right now, when something breaks, the review ends when we figure out who did it. That person apologizes, promises to be more careful, and we close the ticket. Two months later someone else makes the same mistake, because nothing about the system changed. The person got the correction; the deploy script didn't.

I want us to try postmortems that leave names out of the causal story. Write "the deploy script had no confirmation step for production" instead of "Ravi deployed to production by accident." Both sentences describe the same afternoon. Only one of them tells us what to build.

The case for this rests on the quality of what we learn, though it is also kinder. When people expect to be judged, they give the shortest account that survives the meeting. They leave out the part where they were confused, or where they had a hunch and ignored it, or where the runbook said something different from the dashboard. Those are the parts worth having.

Our last three incidents each had a "we knew that was fragile" that nobody put in writing beforehand. We paid for that silence twice.

So here is the concrete proposal. For the next quarter, incidents above sev-2 get a written review within five business days, using a template with no owner field. The facilitator is someone outside the team that was on call. The output is a list of changes to systems and process, each with an owner and a date. Accountability lives there, in the fixes, and we can check whether they shipped.

I'll write the template if there's appetite. Reply here if you'd try it.
