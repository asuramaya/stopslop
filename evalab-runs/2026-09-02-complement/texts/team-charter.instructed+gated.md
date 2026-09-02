# Platform engineering charter

## Why we exist

Product teams here spend somewhere between a fifth and a third of their engineering time on infrastructure nobody chose to specialize in: CI pipelines, secrets rotation, staging environments that drift from production. That work is duplicated across nine teams and done well by none of them. We take it over.

## What we own

We own the paths product engineers walk every day. Build and deploy pipelines. The service scaffold a new backend starts from. Observability defaults, so a service emits useful traces before anyone writes instrumentation. Access to compute, databases, and queues, provisioned through code rather than tickets. We do not own product code, and we do not review it.

If a team wants to run something we do not support, we help them run it and then decide whether to support it. Sometimes that ends in a supported path; sometimes it ends in a documented exception. Both are fine outcomes, and we would rather see the workload than have it hidden from us. The teams doing the strangest things are usually the ones telling us what the platform will need in two quarters, so we would rather be in the room for it.

## How we work

Our users are internal engineers, and we treat them as users. We watch how the tools get used, we read the complaints in #platform-help, and we fix what actually blocks people rather than what is architecturally interesting.

Anything we build must be optional to adopt and easy to leave. A platform that teams route around has told us something; a platform teams cannot escape stops hearing it. We publish a service level for anything on the critical path of a deploy, and we page ourselves when it breaks.

## How to judge us in a year

Time from empty repository to a service in production, measured in hours. Number of deploy-blocking incidents traced to platform components. Fraction of teams on the supported path who chose it rather than were assigned it. If those numbers do not move, the charter was wrong and we should say so.
