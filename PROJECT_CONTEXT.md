# PVL Reservoir Monitor

## Goal

Build a Home Assistant custom integration for current measurements from reservoirs managed by Povodí Vltavy. The first reservoir is Slapy (`VLSL`, `oid=2`). A custom Lovelace card displays current values, recent level history, and the level difference from a selected named reference.

## Verified source

PVL measurement page:

<https://www.pvl.cz/portal/nadrze/cz/pc/Mereni.aspx?id=VLSL&oid=2>

The page is an ASP.NET Web Forms HTML page. The current-values table is rendered in the page response as table `AktualniHodnotyDV`; its timestamp is in `casMereniLbl`. The page's `Mereni.js` script controls layout and graph visibility. No public JSON/XML endpoint was found in the inspected page or script. The integration parses the current HTML table and does not use ASP.NET `__VIEWSTATE`.

PVL's data is provided without guarantee. A blank field means unavailable, not zero. Numeric values use Czech decimal commas. The page reports water levels in the Balt p. v. vertical system.

## Product requirements

- Fetch current PVL values only; do not retrieve PVL historical series.
- Refresh the shared page snapshot every 10 minutes.
- Expose water level, reservoir volume, inflow, outflow, rolling 24-hour precipitation, and air temperature as Home Assistant sensors.
- Let Home Assistant Recorder provide history; the Lovelace card shows the level history for one hour or 24 hours.
- Let users configure multiple named reference levels in the card, switch between them, and see current level minus selected reference.
- Keep the integration and card suitable for HACS distribution. The JS card currently requires manual resource installation; an integration-type HACS repository does not install the root `www/` file.

## Architecture

- `api.py` parses the visible PVL current-values table with Python's standard-library HTML parser.
- `coordinator.py` uses Home Assistant's shared asynchronous HTTP session and a 10-minute `DataUpdateCoordinator`.
- `sensor.py` exposes six sensors. Blank source values make only the corresponding sensor unavailable. The rolling precipitation value is not forced into Recorder when unchanged.
- `www/pvl-reservoir-card.js` reads current sensor states and requests water-level history from Home Assistant; it does not query PVL.
- Named references are configured in the Lovelace card YAML. The selected reference is stored in the browser's local storage, so it is not synchronized between different browsers or devices.

## Current implementation status

The integration, parser, config flow, sensor platform, custom card, parser unit tests, HACS metadata, and user documentation are implemented. The parser tests use Python's standard-library `unittest`. A live PVL response was previously parsed successfully. The workspace does not include Home Assistant, pytest, or a JavaScript runtime, so a full Home Assistant runtime test and automated JavaScript syntax check are unavailable here.

The Git repository has no verified GitHub owner/repository metadata in the integration manifest. `OWNER` references must be replaced with the actual public GitHub owner/repository before publishing through HACS. HACS installs the integration under `custom_components/`; the card must be installed as a dashboard resource separately unless its distribution is moved to a dedicated HACS dashboard repository.

## Directory structure

```text
PVL_Monitor/
├── .gitattributes
├── AGENTS.md
├── PROJECT_CONTEXT.md
├── README.md
├── custom_components/
│   └── pvl_reservoir/
│       ├── __init__.py
│       ├── api.py
│       ├── config_flow.py
│       ├── const.py
│       ├── coordinator.py
│       ├── manifest.json
│       ├── sensor.py
│       └── strings.json
├── hacs.json
├── requirements.txt
├── tests/
│   └── test_api.py
└── www/
    └── pvl-reservoir-card.js
```
