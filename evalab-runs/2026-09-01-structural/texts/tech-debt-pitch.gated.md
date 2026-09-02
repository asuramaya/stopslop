# One quarter of engineering capacity for debt reduction

**To:** Engineering leadership
**From:** [Name], [Team]
**Date:** September 1, 2026

## The ask

Dedicate Q4 engineering capacity to paying down accumulated technical debt, in place of new feature commitments. Bug fixes and customer escalations continue as normal.

## Why now

Our velocity is dropping for reasons that have nothing to do with the team. Three examples:

- The checkout service has no test coverage below the integration layer. Every change there requires manual QA, which adds three to five days to work that used to ship in one.
- We run two authentication paths because the migration begun last year was never finished. New endpoints need both, and we get this wrong often enough that it now accounts for a recurring share of production incidents.
- Build times have grown past fifteen minutes, so people batch changes into larger, riskier merges.

None of these will surface as a project. They surface as estimates getting longer and nobody able to say why.

## What we would do

Finish the auth migration and delete the old path. Bring checkout to a coverage level where changes can ship without manual QA. Cut CI time by splitting the monolithic test job.

## What it costs, and what it returns

One quarter of feature work, deferred rather than cancelled. In exchange we expect estimates on checkout work to return to earlier levels, one class of incident to disappear, and CI to stop shaping how people merge. That last one matters more than it sounds: merge size drives review quality, and review quality drives everything downstream of it.

## The alternative

We keep paying this in slower quarters, without a line item that names it.

I'm happy to walk through the numbers behind any of the above.
