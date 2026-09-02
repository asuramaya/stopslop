# Charter: Platform Engineering

## Who we are

Six engineers, formed on 2026-09-02, reporting to the VP of Engineering. We build and run the systems other engineers at this company build on: CI pipelines, deployment tooling, the Kubernetes clusters, secrets management, and the observability stack.

## What we own

We own these systems end to end. When a deploy pipeline breaks at 2am, we get paged, not the product team whose service failed to ship. We publish an on-call rotation and answer within fifteen minutes during business hours, one hour overnight.

We do not own product code. If a service leaks memory, we will help you find it and we will give you the flame graphs, but the team who wrote the service fixes the service.

## How we decide

We treat product teams as customers who can leave. If someone builds their own deploy script around ours, we failed, and we go ask them why before we ask them to stop.

We write down decisions that change interfaces other teams depend on. Two engineers review each one. We ship the smallest version that works and let the next quarter's usage tell us what to build after that.

## What we promise

Ninety-nine percent availability on the build system and the internal package registry, measured monthly and published on a dashboard anyone can open. Two weeks notice before we break an interface, with a migration path we have tested ourselves.

## What we ask

Tell us when our tools slow you down. File the ticket, drop it in #platform, or stop one of us in the hallway. We would rather hear about a rough edge on the day you hit it than read about it in a survey six months later.
