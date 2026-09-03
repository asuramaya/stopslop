Slots in right after the 409 paragraph, since both are about the server telling you no:

> The server also says no if you ask too often. There is a limit on how many requests you can send per minute, and going over it gets you error 429 plus a `Retry-After` header saying how many seconds to wait. Wait that long, then try the same request again. Most people hit this by checking availability one day at a time in a loop. Ask for the whole range at once instead.

I left the actual number out rather than invent one; drop your real per-minute limit into the second sentence. The 429 code and `Retry-After` header are the standard way to do this, but if your service signals rate limits some other way, tell me and I'll correct it.
