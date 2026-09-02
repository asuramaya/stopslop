No API was named, so this is written to be dropped in and specialised with your own resource names.

## Design philosophy

Four commitments, and every endpoint answers to them.

Resources are nouns, and they behave the same way everywhere. If you learn how to list, filter, and paginate one collection, you know how to do it for all of them. Query parameters keep their names and meanings across resources. We would rather repeat a familiar pattern than invent a clever one for a single case. Responses are explicit in the same spirit: we do not omit a field because it is null, and we do not change a field's type depending on context. An absent value is spelled out, so your deserialiser never has to guess.

Errors are written for the person debugging at 2am. Every failure returns a stable machine-readable code, the specific field or parameter at fault, and a sentence describing what to do differently. HTTP status codes mean what the specification says they mean.

Changes are additive. New fields and new optional parameters can appear in a minor release. Anything that would break a working integration goes behind a version, with a migration note and a deprecation window stated in months, not in vague future terms. When these commitments conflict, predictability wins.
