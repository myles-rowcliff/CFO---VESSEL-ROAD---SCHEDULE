# CLAUDE.md – CFO Vessel Schedule (POM · Aiambak · Kiunga)

Notes for Claude Code sessions working in this repo. The repo is **public** – never commit tokens, passwords, email addresses or internal links.

## What this is

OKTL's diesel (CFO) supply schedule for the Tabubil mine site. It estimates lead times for CFO travelling POM → Aiambak by ship, then Aiambak → Kiunga by river vessel or by truck convoy. The website in `docs/` is published with GitHub Pages and is shared with people outside OKTL.

The owner is Myles (OKTL). The master copies of the schedule Sheet, the internal dashboard and the written Summary live in a claude.ai project ("AIAMBAK - CFO SCHEDULE") that Claude Code can't reach. Schedule changes are normally worked out there. In a Claude Code session the usual jobs are committing updated files, or re-running the engine here when Myles gives a change directly.

## Repo layout

| Path | Contents |
| --- | --- |
| `docs/index.html` | The website: an interactive dashboard (Overview, Scheduled vs actual, Time & motion, Site fuel, Amigo 1, Summary). The Fleet tab is hidden (Myles, 19 Nov 2026) but `fleet.json` is still kept up to date. The Summary tab has Daily / Weekly / Fortnightly / Overall buttons: the first three are worked out in the page from the data files; Overall is the written text inline in `<div id="sumOverall">`. |
| `docs/data/*.json` | Website data: `fly`, `river`, `amigo`, `site` (generated), `fleet`, `amigoset`, `sva`, `meta` (edited by hand). |
| `docs/d3.min.js`, `docs/logo.png`, `docs/.nojekyll` | Bundled so the site needs nothing from outside. |
| `engine/engine.py` | Hour-by-hour simulation of every vessel and truck. Reads `params.json` (or the `PFILE` env var) and writes `engine_out.json` to the current folder. |
| `engine/params.json` | Current inputs: vessel positions, capacities, trucks, convoys, site use. |
| `engine/baseline_19nov.json` | The plan **locked on 19 Nov 2026** for scheduled vs actual. **Never overwrite or regenerate it.** |
| `engine/build.py` | Builds the Excel version of the schedule (for the claude.ai Sheet). |
| `data/engine_out.json` | The latest engine run. `data/d_sva.json` = scheduled vs actual data. |
| `tools/make_data.py` | Writes `docs/data/{fly,river,amigo,site}.json` from `engine_out.json`. |
| `tools/akchart.py` | Chart helper. |

GitHub Pages: branch `main`, folder `/docs`. The site republishes about a minute after a push.

## Updating the schedule

```bash
cd engine && python engine.py          # writes engine/engine_out.json
cp engine_out.json ../data/engine_out.json && cd ..
python tools/make_data.py data/engine_out.json docs/data
```

Then by hand: update `docs/data/fleet.json` (last known event per vessel), set `docs/data/meta.json` `updated` to the run time (PNG time, UTC+10), and bring the Summary section of `docs/index.html` into line with the new figures. Data files use `{"value": {"rows": {"1": [header...], "2": [...], ...}}}`.

## Scheduled vs actual

- The comparison starts 19 Nov 2026 and uses the locked baseline. Actual litres to Kiunga (river and truck) go into `docs/data/sva.json`; `null` means not entered yet.
- Rebuilding the schedule never changes the baseline or the actuals.
- **Direct runs (Myles, 19 Nov 2026):** when a vessel is sent straight from Aiambak to Kiunga, add its litres to "Scheduled by river (L)" in `docs/data/sva.json` (and `data/d_sva.json`) on the day it discharges at Kiunga, and list it in the note under the tab heading in `docs/index.html`. Leave `engine/baseline_19nov.json` untouched. Done so far: Fly Challenger 1,200,000 L on 22 Nov.

## Planning rules (confirmed by Myles)

- **POM → Aiambak:** Fly Challenger, Fly Resilience, Fly Prosperity (1.5 ML each from their next loading), Fly Warrior (1.0 ML). Round trip 9 days (4 days each way + 1 day alongside at Aiambak) plus 1 day loading at POM. A Fly vessel doesn't leave Aiambak until all its CFO is off, so it waits when Amigo 1 is full.
- **Diamond:** 950,000 L, runs POM → Aiambak like a Fly vessel (12 h discharging).
- **Wonderland:** 700,000 L shuttle POM → Aiambak into Amigo 1 from 5 Dec 2026, 9-day cycle.
- **Aiambak → Kiunga (river):** Elimbari (1.0 ML). Round trip 5 days (2.5 each way) plus 12 h loading at Aiambak and 12 h discharging at Kiunga. River vessels get first call on Fly/Diamond CFO at Aiambak; the rest goes into Amigo 1.
- **Amigo 1** (storage at Aiambak): capacity 2.1 ML.
- **Trucks:** 40,000 L each, from Amigo 1 to Kiunga, 7 h. From 20 Nov 2026, 14 trucks a day in three convoys: A 5 AM (6), B 6 AM (4), C 7 AM (4). Truck turnaround **16 h (confirmed)**. A truck that can't be fuelled waits for the next convoy.
- **Site use:** 350,000 L a day.
- **Kiunga / Tabubil storage:** treat as **unlimited** until Myles says otherwise. Don't list it as a risk.
- **Tank-tainers** come off freight vessels discharged at Aiambak. They are not part of the schedule; don't model or mention their source. Gravity-feed them only if Myles says so.
- **Johnny Traveller:** not relevant to the schedule; don't include or mention it.

## Decisions

- **Fly Challenger (19 Nov 2026):** one-off run. Left Aiambak 8 AM 19 Nov with 1.2 ML direct to Kiunga (3 days up, 12 h discharge, 3 days back to Aiambak, 4 days on to POM), then normal POM → Aiambak trips. In `params.json`: event `Passed Aiambak to Kiunga`, `t_ak` 3, `t_ka` 3, `dis_k` 0.5, `depart_aia` true, `since` 2026-11-18T13:00.
- **Fly Resilience (19 Nov 2026):** tops up Amigo 1 with its 1.5 ML (event `Standby at Aiambak` = discharging at Aiambak), then normal trips.

## Style

- Plain language for a logistics audience; litres with thousands separators; dates like "19 Nov"; times in PNG time (UTC+10).
- On the website, don't show or mention the hidden Arrivals and River voyages views.
