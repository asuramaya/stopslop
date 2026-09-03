Short warning, in the same plain register as the rewritten auth paragraph. It goes right after it, since a first-timer hits 401 and 429 in the same debugging session.

There is also a cap on how many requests you can send in a given minute. Go past it and the API answers 429 instead of your data, with a `Retry-After` header telling you how many seconds to wait. Wait that long, then try the request again. Do not retry immediately in a loop, because failed attempts count too and the wait grows. Most people hit the cap by checking availability over and over; storing the answer for a few seconds fixes it.

Check three things against your real API before this ships: whether the window is per minute, whether `Retry-After` is actually returned (some APIs send `X-RateLimit-Reset` instead), and whether rejected requests count toward the limit. That last one is the reason for the "do not retry in a loop" sentence, so if rejects are free, drop that sentence.

There is one knock-on further down. The intro's closing line promises "rate limits at the end," which still holds, but that line should now say the section covers the per-endpoint numbers, so a reader doesn't think it repeats this.
