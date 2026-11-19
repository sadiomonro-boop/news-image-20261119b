# The World Today — 19 November 2026 (Variant B)

make.fun `news-image-20261119` entry: one image summing up Thursday
19 November 2026 world news. Variant B uses a world-map layout — six
regional panels (North America, South America, Europe, Africa, Asia,
Oceania + Middle East), a hero story, a BY THE NUMBERS strip and a
top-headlines ticker. 31 verified stories from 6 continents.

## Run

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

Pure Python 3.13 standard library (own 5x7 bitmap font, own PNG writer
via `zlib`/`struct`). No network. Deterministic: two runs produce
byte-identical output (verified).

## Output

- 1024x1024 PNG, 157,522 bytes (limit 1 MiB)
- Rendered image: `render-final.png` (same bytes as `main.py` produces)

## Sources

Stories were verified against live web reporting on 19 Nov 2026
(events of 18–19 Nov 2026, first reported that day). See
`BUILD-REPORT.json` for the full story list and checks.
