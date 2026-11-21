# CLAUDE.md – CFO Vessel Schedule (POM · Aiambak · Kiunga)

Notes for Claude Code sessions working in this repo. The repo is **public** – never commit tokens, passwords, email addresses or internal links.

## What this is

OKTL's diesel (CFO) supply schedule for the Tabubil mine site. It estimates lead times for CFO travelling POM → Aiambak by ship, then Aiambak → Kiunga by river vessel or by truck convoy. The website in `docs/` is published with GitHub Pages and is shared with people outside OKTL.

The owner is Myles (OKTL). The master copies of the schedule Sheet, the internal dashboard and the written Summary live in a claude.ai project ("AIAMBAK - CFO SCHEDULE") that Claude Code can't reach. Schedule changes are normally worked out there. In a Claude Code session the usual jobs are committing updated files, or re-running the engine here when Myles gives a change directly.

## Repo layout

| Path | Contents |
| --- | --- |
| `docs/index.html` | The website: an interactive dashboard (Overview, Convoy manifest, Scheduled vs actual, Time & motion, Site fuel, Amigo 1, Summary). The Fleet tab is hidden (Myles, 19 Nov 2026) but `fleet.json` is still kept up to date. Scheduled vs actual and the Site fuel tab's Projected site stock chart have Weekly / Fortnightly / Overall buttons. The Convoy manifest tab lists sent convoys (date, time, reference, trucks, litres, ETA) with View / Print (anyone) and Edit / Delete (token holders); **Add convoy** opens a form (departure date, time, convoy reference – default AIA-C-YYYYMMDD-NN – number of trucks, then truck number, tanker number and litres loaded per truck). View shows a printable sheet (Ok Tedi Mining logo, site theme, A4 landscape). **Manifests are saved to the repo** in `docs/data/convoys.json` by the page itself through the GitHub API, using a token Myles keeps in his browser; each save also sets `Actual by truck (L)` in `docs/data/sva.json` (and `data/d_sva.json`, and the `meta.json` note) to the sum of that day's manifests, dated by ETA Kiunga (departure + 7 h). Overview tiles: Scheduled CFO to Kiunga today (current schedule – same figure as Scheduled vs actual), Actual CFO reaching Kiunga today (from `sva.json` actuals – river by hand, truck from manifests), Kiunga/Tabubil stock today, CFO to Kiunga next 7 days. The Summary tab has Daily / Weekly / Fortnightly / Overall buttons: the first three are worked out in the page from the data files; Overall is the written text inline in `<div id="sumOverall">`. |
| `docs/data/*.json` | Website data: `fly`, `river`, `amigo`, `site` (generated), `fleet`, `amigoset`, `sva`, `meta`, `notes` (edited by hand). `notes.json` holds dated notes of what actually happened (Date, Note); they show under "What happened" in the Summary's Daily/Weekly/Fortnightly views. |
| `docs/d3.min.js`, `docs/logo.png`, `docs/.nojekyll` | Bundled so the site needs nothing from outside. |
| `engine/engine.py` | Hour-by-hour simulation of every vessel and truck. Reads `params.json` (or the `PFILE` env var) and writes `engine_out.json` to the current folder. |
| `engine/params.json` | Current inputs: vessel positions, capacities, trucks, convoys, site use. |
| `engine/baseline_19nov.json` | The plan **locked on 19 Nov 2026** for scheduled vs actual. **Never overwrite or regenerate it.** |
| `engine/build.py` | Builds the Excel version of the schedule (for the claude.ai Sheet). |
| `data/engine_out.json` | The latest engine run. `data/d_sva.json` = scheduled vs actual data. |
| `tools/make_data.py` | Writes `docs/data/{fly,river,amigo,site}.json` from `engine_out.json`. |
| `tools/akchart.py` | Chart helper. |

GitHub Pages: branch `main`, folder `/docs`. The site republishes about a minute after a push.

## The website writes to `main`

Editing manifests: with a GitHub token in the browser (Myles), or – with a **passcode** (`SAVE_URL` in `docs/index.html` = https://cfo---vessel-road---schedule.myles-rowcliff.workers.dev) checked by the save service in `worker/convoy-worker.js` (a Cloudflare Worker holding its own token; setup in `worker/README.md`). The passcode is remembered per computer. The service only writes manifests and the truck actuals they set.

The Convoy manifest tab commits to `main` (convoys.json, sva.json, d_sva.json, meta.json). **Before editing any of those files, `git fetch origin main` and merge it**, and never overwrite convoys.json or the truck actuals it sets. When publishing a branch, merge `origin/main` first if a fast-forward isn't possible. Truck actuals now come from the manifests (Myles, 20 Nov 2026); river actuals and site stock are still entered by hand.

## Updating the schedule

```bash
cd engine && python engine.py          # writes engine/engine_out.json
cp engine_out.json ../data/engine_out.json && cd ..
python tools/make_data.py data/engine_out.json docs/data
```

Then by hand: update `docs/data/fleet.json` (last known event per vessel), set `docs/data/meta.json` `updated` to the run time (PNG time, UTC+10), and bring the Summary section of `docs/index.html` into line with the new figures. Data files use `{"value": {"rows": {"1": [header...], "2": [...], ...}}}`.

## Scheduled vs actual

- **Scheduled = the current schedule** (Myles, 21 Nov 2026): the page takes each day's scheduled river and truck litres from `site.json` (River/Truck arrivals of the latest engine run), so the tab, the Overview's scheduled tile and the Summary all follow every schedule update. The locked plan (`baseline_19nov.json`, and the Scheduled columns in `sva.json`) is kept but no longer shown; the direct-run additions below were for the old locked comparison.
- The comparison starts 19 Nov 2026. The chart always shows the **daily target of 560,000 L** (14 trucks; Myles, 21 Nov 2026) as a green dashed line. Actual litres to Kiunga (river and truck) go into `docs/data/sva.json`; `null` means not entered yet.
- Rebuilding the schedule never changes the baseline or the actuals.
- **Site stock:** the scheduled vs actual site stock panel on the Site fuel tab is hidden for now (Myles, 19 Nov 2026; `<section id="sitesva">` without the `cfo-page` class). Keep its data up to date. `docs/data/sitesva.json` has scheduled closing stock (locked plan plus changes made in `sva.json`) and actual closing stock, entered by hand (`null` = not entered). After changing scheduled figures in `sva.json`, run `python tools/make_sitesva.py` from the repo root; it keeps the actuals.
- **Direct runs (Myles, 19 Nov 2026):** when a vessel is sent straight from Aiambak to Kiunga, add its litres to "Scheduled by river (L)" in `docs/data/sva.json` (and `data/d_sva.json`) on the day it discharges at Kiunga, and list it in the note under the tab heading in `docs/index.html`. Leave `engine/baseline_19nov.json` untouched. Done so far: Fly Challenger 1,200,000 L on 22 Nov; Fly Resilience 1,500,000 L on 23 Nov.

## Planning rules (confirmed by Myles)

- **POM → Aiambak:** Fly Challenger, Fly Resilience, Fly Prosperity (1.5 ML each from their next loading), Fly Warrior (1.0 ML). Round trip 9 days (4 days each way + 1 day alongside at Aiambak) plus 1 day loading at POM. A Fly vessel doesn't leave Aiambak until all its CFO is off, so it waits when Amigo 1 is full.
- **Diamond:** 950,000 L, runs POM → Aiambak like a Fly vessel (12 h discharging).
- **Wonderland:** 700,000 L shuttle POM → Aiambak into Amigo 1 from 5 Dec 2026, 9-day cycle.
- **Aiambak → Kiunga (river):** Elimbari (1.0 ML). Round trip 5 days (2.5 each way) plus 12 h loading at Aiambak and **7 h discharging at Kiunga** (Myles, 20 Nov 2026 – was 12 h; `dis_k` in `params.json`, `DISK_H` in `docs/index.html`). River vessels get first call on Fly/Diamond CFO at Aiambak; the rest goes into Amigo 1.
- **Amigo 1** (storage at Aiambak): capacity 2.1 ML.
- **Trucks:** 40,000 L each, from Amigo 1 to Kiunga, 7 h. From 20 Nov 2026, 14 trucks a day in three convoys: A 5 AM (6), B 6 AM (4), C 7 AM (4). Truck turnaround **16 h (confirmed)**. A truck that can't be fuelled waits for the next convoy.
- **Site use:** 350,000 L a day.
- **Kiunga / Tabubil storage:** treat as **unlimited** until Myles says otherwise. Don't list it as a risk.
- **Tank-tainers** come off freight vessels discharged at Aiambak. They are not part of the schedule; don't model or mention their source. Gravity-feed them only if Myles says so. Diesel tank-tainers sent to Kiunga are **pre-filled** unless Myles says otherwise, so they don't draw on Amigo 1 (in `params.json` `extra_loads`, set the third value to `false`).
- **Johnny Traveller:** not relevant to the schedule; don't include or mention it.

## Decisions

- **Fly Challenger (19 Nov 2026):** one-off run. Left Aiambak 8 AM 19 Nov with 1.2 ML direct to Kiunga (3 days up, 7 h discharge, 3 days back to Aiambak, 4 days on to POM), then normal POM → Aiambak trips. In `params.json`: event `Passed Aiambak to Kiunga`, `t_ak` 3, `t_ka` 3, `dis_k` 7/24, `depart_aia` true, `since` 2026-11-18T13:00.
- **Fly Resilience (20 Nov 2026):** one-off run. Never discharged at Aiambak; left Aiambak 8:30 AM 20 Nov with 1.5 ML direct to Kiunga (same river times as Challenger: 3 days each way, 7 h discharge), then 4 days on to POM and normal trips. In `params.json`: event `Passed Aiambak to Kiunga`, `depart_aia` true, `since` 2026-11-18T14:00.
- **Diamond, first trip (19 Nov 2026):** discharges all 950,000 L into Amigo 1 at Aiambak on 23 Nov instead of refuelling Elimbari (`amigo_only: [1]` on Diamond in `params.json`).
- **Elimbari one-off trip to POM (19 Nov 2026):** Elimbari arrived at Kiunga 4 PM 20 Nov but only started discharging 3 PM 21 Nov (`dis_start`); back at Aiambak empty about 10 AM 24 Nov, it sails to POM, loads 1.0 ML and goes straight to Kiunga (about 11 PM 5 Dec), then normal Aiambak – Kiunga runs (`pom_once` on Elimbari in `params.json`). Assumes Fly vessel sailing times and 1 day loading at POM.
- **Road closed (20 Nov 2026):** no convoys on 20 or 21 Nov (poor road conditions); assumed to reopen 6 AM 22 Nov unless Myles says otherwise (`road_closed` in `params.json`). Trucks due during a closure wait at Aiambak and go with the first convoy after.
- **Daily truck target stays 14** (Myles, 20 Nov 2026), even with a tanker down for maintenance, unless Myles says to change it.
- **Fly Challenger at Kiunga (21 Nov 2026):** arrives about 6 PM 21 Nov (`eta_k`), starts discharging 1 h after Elimbari finishes, 11 PM (`dis_start`).
- **Amigo 1 confirmed 1,170,000 L (21 Nov 2026).**
- **Fly Warrior and Fly Prosperity delayed 2 days at POM (21 Nov 2026):** Warrior loads from midday 23 Nov (`date`), Prosperity from midday 24 Nov (`hold` 3).
- **Diamond delayed at POM (20 Nov 2026):** loading starts midday 22 Nov.
- **12 trucks filled from Amigo 1, evening 19 Nov (480,000 L)** for the 20 Nov convoys: `prefill` in `params.json`.

## Engine inputs worth knowing

- `fly[].dis_from`: a vessel alongside at Aiambak (event `Standby at Aiambak`) doesn't discharge before this time.
- `fly[].amigo_only`: voyage numbers whose CFO all goes into Amigo 1, not to river vessels.
- `river[].pom_once`: the first time the river vessel is back at Aiambak empty before this time, it sails to POM (t_back), loads (load_pom) and goes straight to Kiunga (t_out + t_ak).
- `dis_start` (river vessels and direct runs) / `eta_k` (direct runs): arrival at Kiunga and when discharging starts can differ (waiting at Kiunga); river data has a `Discharge start` column.
- `road_closed`: `[[from, to]]` times the road is closed; no convoys leave Aiambak in that window.
- `prefill`: `[[time, litres]]` trucks filled from Amigo 1 ahead of their convoy; the next convoys use them first.
- Amigo 1 daily data has two truck figures: `Filled from Amigo 1 (L)` (what leaves the tank that day, drives stock) and `Trucks sent to Kiunga (L)` (what leaves Aiambak by truck that day, including pre-filled trucks and tank-tainers). Short convoy days are judged on trucks sent.
- River deliveries to Kiunga are spread over the 7 h discharge, except one that runs past midnight: that is counted in full on the day it finishes (Myles, 19 Nov 2026), so it isn't split across two days.
- `extra_loads`: `[[time, litres, from_amigo]]` one-off loads such as tank-tainers.

## Style

- Plain language for a logistics audience; litres with thousands separators; dates like "19 Nov"; times in PNG time (UTC+10).
- On the website, don't show or mention the hidden Arrivals and River voyages views.
