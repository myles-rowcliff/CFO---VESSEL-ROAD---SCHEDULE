# CFO Vessel Schedule – POM · Aiambak · Kiunga

The OKTL diesel (CFO) supply schedule for the Tabubil site: Fly vessels, Diamond and Wonderland from POM to Aiambak, Elimbari from Aiambak to Kiunga, and truck convoys from Amigo 1 to Kiunga. Site use is 350,000 L a day.

**Website:** https://myles-rowcliff.github.io/CFO---VESSEL-ROAD---SCHEDULE/ – interactive Overview, Scheduled vs actual, Time & motion, Site fuel, Amigo 1, Fleet and Summary tabs, with week toggles and hover details.

## What's in here

| File / folder | Contents |
| --- | --- |
| `docs/` | The website (published by GitHub Pages). `index.html` reads its numbers from `docs/data/` every time someone opens it. |
| `docs/data/` | `fly`, `river`, `amigo`, `site`, `fleet`, `amigoset` (the schedule), `sva` (scheduled vs actual litres to Kiunga; null = not entered yet), `meta` (date of the last update). |
| `engine/` | The schedule model: `engine.py` simulates every vessel and truck hour by hour from `params.json`; `baseline_19nov.json` is the plan locked on 19 Nov for scheduled vs actual (never overwrite it). |
| `data/` | `engine_out.json` is the latest engine run. |
| `tools/` | `make_data.py` turns `engine_out.json` into the website data files. |
| `CLAUDE.md` | Planning rules and update steps for Claude Code sessions. |

## How updates work

Changes and actuals go to Claude. Claude re-runs the schedule, updates `docs/data/` (and `engine/` if the plan changed) and commits. GitHub Pages republishes the site about a minute later; anyone with the link sees the new figures when they refresh.

GitHub Pages settings: *Deploy from a branch*, branch `main`, folder **`/docs`**.
