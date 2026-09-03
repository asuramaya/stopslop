```python
import csv
from typing import Any


def read_csv_rows(
    path: str,
    fieldnames: list[str] | None = None,
    fill: Any = None,
    encoding: str = "utf-8",
) -> list[dict[str, Any]]:
    """Read a CSV file into a list of dicts.

    Short rows are padded with `fill` so every dict has the full set of keys.
    Extra columns beyond the header land under the key ``"_extra"`` as a list.
    If `fieldnames` is None, the first non-empty row is used as the header.
    """
    rows: list[dict[str, Any]] = []

    # newline="" is required by csv: it handles embedded newlines and a
    # missing final newline without inventing or dropping a record.
    with open(path, newline="", encoding=encoding) as handle:
        reader = csv.reader(handle)

        header = fieldnames
        if header is None:
            for raw in reader:
                if any(cell.strip() for cell in raw):
                    header = [cell.strip() for cell in raw]
                    break
            if header is None:
                return rows

        width = len(header)
        for raw in reader:
            if not raw or not any(cell.strip() for cell in raw):
                continue

            values = raw[:width]
            if len(values) < width:
                values = values + [fill] * (width - len(values))

            record: dict[str, Any] = dict(zip(header, values))
            if len(raw) > width:
                record["_extra"] = raw[width:]

            rows.append(record)

    return rows
```
