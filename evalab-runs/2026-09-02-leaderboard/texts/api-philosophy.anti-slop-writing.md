## Design philosophy

We picked boring over clever, and we'd pick it again.

Every endpoint returns the same envelope shape, even when that wastes a few bytes. Errors come back with an HTTP status, a stable machine-readable code, a human sentence you can paste into a bug report without editing it, and the request id. There's no batch endpoint. If you need to create forty records, call create forty times, in parallel if you want; we'd rather you write a for-loop than learn our partial-failure semantics.

Nothing is ever removed from a response. Fields get added, old ones stick around long past their usefulness, marked deprecated in the changelog and left untouched in the payload. Ugly? Sure. But your parser from 2023 still works.

Pagination is cursor-based everywhere, never offset-based, because offsets lie to you when rows shift underneath.

The one place we break our own rules is auth, which uses a scheme nobody loves and everybody recognizes. That was deliberate. Familiarity won that argument, and it wasn't close.

What we won't do is guess. No implicit type coercion, no quietly defaulting a missing field to something plausible. Send us a malformed request, get a 400 back with the JSON path that broke.
