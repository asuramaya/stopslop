```python
import csv


def read_csv_rows(path, fieldnames=None, fill=None, encoding="utf-8-sig"):
    """Read a CSV file into a list of dicts, one per data row.

    The header line supplies the keys unless `fieldnames` is given, in which
    case the file is assumed to have no header. Rows with fewer columns than
    the header are padded with `fill`; extra columns land under the key None,
    matching csv.DictReader's restkey behaviour.

    A missing trailing newline on the last line needs no special handling --
    the csv module yields that line like any other -- but a trailing blank
    line does, so empty rows are skipped.
    """
    with open(path, "r", newline="", encoding=encoding) as fh:
        reader = csv.reader(fh)

        if fieldnames is None:
            try:
                fieldnames = next(reader)
            except StopIteration:
                return []
            fieldnames = [name.strip() for name in fieldnames]
        else:
            fieldnames = list(fieldnames)

        width = len(fieldnames)
        rows = []
        for values in reader:
            if not values or (len(values) == 1 and not values[0].strip()):
                continue
            row = dict(zip(fieldnames, values))
            if len(values) < width:
                for name in fieldnames[len(values):]:
                    row[name] = fill
            elif len(values) > width:
                row[None] = values[width:]
            rows.append(row)
        return rows
```

Two notes on the choices:

`newline=""` is what makes quoted fields containing newlines parse correctly — the csv module wants to see the raw line endings. `utf-8-sig` strips a BOM if a spreadsheet export left one, which otherwise shows up glued to the first header name.

The missing-trailing-newline case works out of the box; what actually breaks naive readers is the *blank* line, so that's the branch that's explicit.

I ran it on `a,b,c` with a short row, a blank line, an over-long row, and no final newline:

```
{'a': '1', 'b': '2', 'c': '3'}
{'a': '4', 'b': '5', 'c': None}
{'a': '6', 'b': '7', 'c': '8', None: ['9']}
```

An empty file returns `[]`. The scratch copy is at `/tmp/csvfn/read_rows.py` — I didn't add anything to the repo. Say the word if you want it dropped somewhere in `src/evalab/`.
