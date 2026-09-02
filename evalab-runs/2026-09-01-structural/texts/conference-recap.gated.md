Four of us went to [Conference], and we came back arguing. That's the good outcome.

The talks we expected to matter mostly didn't. Three separate keynotes covered the same ground on agent orchestration, and by the third one we were skipping ahead to the Q&A, which is where the real information lives. Someone from a mid-size logistics company stood up and said their team had ripped out their vector database and gone back to Postgres full-text search. The room went quiet. Nobody on stage had a good answer.

That was the week's actual theme, though nobody put it on a slide: the gap between what gets presented and what's running in production is about eighteen months wide.

Three things we're bringing home.

First, evaluation is the bottleneck, not the models. Every team we talked to in the hallway track described the same failure. They can ship a change in a day and can't tell for three weeks whether it helped. We have this problem too.

Second, small models are doing more than we assumed. Two teams described routing 70-80% of traffic to a cheaper model with a fallback path, and neither had fielded a quality complaint from users.

Third, nobody has solved observability. Not the vendors, not the platform teams. We sat through six dashboard demos and none of them would have caught the bug we shipped in March.

Thursday afternoon is blocked out to go through notes and pick one thing to actually try.

You gave me no conference, industry, or team, so I picked a concrete framing — an AI-infrastructure event, an engineering team — because specifics are what keep a recap from reading like filler. Swap `[Conference]`, the three takeaways, and the March bug for your real ones; the structure holds. Draft is at `/tmp/recap.md`.
