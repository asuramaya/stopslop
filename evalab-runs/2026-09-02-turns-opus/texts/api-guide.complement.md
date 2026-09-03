## Rate limits

Each token allows 100 requests per minute. Go over that and you get a 429 response with a `Retry-After` header telling you how many seconds to wait. Availability queries across long date ranges count double, so a widget that polls open slots on every keystroke will hit the ceiling fast. Cache availability for a few seconds on your side and back off when a 429 arrives.
