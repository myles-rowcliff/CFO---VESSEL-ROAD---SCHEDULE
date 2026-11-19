# CFO Vessel Schedule – POM · Aiambak · Kiunga

The OKTL diesel (CFO) supply schedule for the Tabubil site: Fly vessels and Diamond/Wonderland from POM to Aiambak, Elimbari from Aiambak to Kiunga, and tanker convoys from Amigo 1 to Kiunga. Site use is 350,000 L a day.

**Website:** `docs/`, published with GitHub Pages. It's interactive: Overview, Scheduled vs actual, Time & motion, Site fuel, Amigo 1, Fleet and Summary tabs, with week toggles and hover details.

## What's in here

| Folder | Contents |
| --- | --- |
| `docs/index.html` | The website. It reads its numbers from `docs/data/` every time someone opens it. |
| `docs/data/` | The data: `fly`, `river`, `amigo`, `site`, `fleet`, `amigoset` (the schedule), `sva` (scheduled vs actual litres to Kiunga; null = not entered yet), `meta` (date of the last update). |
| `docs/d3.min.js`, `docs/logo.png` | Chart library and logo, kept in the repo so the site needs nothing from outside. |
| `engine/` | The schedule model: `engine.py` simulates every vessel and truck hour by hour from `params.json`. `build.py` makes the Excel schedule. `baseline_19nov.json` is the plan locked on 19 Nov for scheduled vs actual. Never overwrite it. |
| `data/engine_out.json` | Raw output of the latest model run. |
| `tools/akchart.py` | Aiambak – Kiunga time and motion chart as an image. |

## How updates work

Changes and actuals are given to Claude in the "AIAMBAK - CFO SCHEDULE" project. Claude updates the files in `docs/data/` (and the model if the plan changed) and commits them. GitHub Pages republishes the site about a minute later. Anyone with the link sees the new figures when they refresh the page.

## Turning on GitHub Pages (one-off)

1. The repo must be **public** on a free GitHub account.
2. In the repo go to **Settings → Pages**.
3. Set **Source** to *Deploy from a branch*, **Branch** to `main` and the folder to `/docs`. Save.
4. After a minute or two the site is at `https://<your-username>.github.io/<repo-name>/`.

Anyone with the link can view the site and the repo.
