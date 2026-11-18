# PVL Reservoir Monitor

Home Assistant custom integration for current measurements from VD Slapy, published by Povodí Vltavy.

## Features

- Reads current values from the public PVL measurements page every 10 minutes.
- Creates sensors for water level, volume, inflow, outflow, 24-hour precipitation, and air temperature.
- Uses Home Assistant Recorder for history. The integration does not download historical measurements from PVL.
- Includes a responsive Lovelace card with a configurable water-level gauge, hydrological readings, one-hour and 24-hour charts, and named reference levels.

## Data source and parsing

The integration requests:

<https://www.pvl.cz/portal/nadrze/cz/pc/Mereni.aspx?id=VLSL&oid=2>

The inspected page returns an ASP.NET Web Forms HTML page with its current-values table rendered in the response. No public JSON/XML endpoint was found in the page or its `Mereni.js` script. The integration parses the visible current-values table and does not depend on the page's `__VIEWSTATE` field.

PVL warns that its measurements are provided without guarantee. The page uses decimal commas. Empty fields are exposed as unavailable sensors rather than zero.

## Installation

### Manual integration installation

Copy `custom_components/pvl_reservoir` into the `custom_components` directory under your Home Assistant configuration directory, then restart Home Assistant. Add **PVL Reservoir Monitor** from **Settings → Devices & services → Add integration**.

### Dashboard card

Copy `www/pvl-reservoir-card.js` to the `www` directory under your Home Assistant configuration directory. Add it as a JavaScript module resource at `/local/pvl-reservoir-card.js`.

An integration-type HACS repository installs the integration folder, not the root-level `www` card file. HACS users therefore need to install/register the card separately, or use a future dedicated HACS dashboard repository for the card.

## Lovelace card configuration

The card uses YAML configuration and does not require a frontend framework or visual editor. Add the resource `/local/pvl-reservoir-card.js` as a JavaScript module, then add a manual card with a configuration such as:

```yaml
type: custom:pvl-reservoir-card
name: VD Slapy
level_entity: sensor.pvl_reservoir_slapy_water_level
inflow_entity: sensor.pvl_reservoir_slapy_inflow
outflow_entity: sensor.pvl_reservoir_slapy_outflow
volume_entity: sensor.pvl_reservoir_slapy_volume
precipitation_24h_entity: sensor.pvl_reservoir_slapy_precipitation_24h
air_temperature_entity: sensor.pvl_reservoir_slapy_air_temperature
min_level: 220
max_level: 273
show_history: true
references:
  - name: Hladina stálého nadržení
    level: 246.6
  - name: Kóta přelivu
    level: 262.6
  - name: Maximální retenční hladina
    level: 270.6
```

The entity IDs above correspond to the entities defined by this integration. Entity IDs can be changed in Home Assistant, so check **Settings → Devices & services → PVL Reservoir Monitor** if one is different. All entity parameters are optional and default to the integration's Slapy entities. A missing or unavailable entity is displayed as unavailable without breaking the card.

### Supported card options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | string | `VD Slapy` | Card heading. |
| `level_entity` | entity ID | `sensor.pvl_reservoir_slapy_water_level` | Water-level sensor used by the gauge, difference, and history chart. |
| `inflow_entity` | entity ID | `sensor.pvl_reservoir_slapy_inflow` | Current inflow sensor. |
| `outflow_entity` | entity ID | `sensor.pvl_reservoir_slapy_outflow` | Current outflow sensor. |
| `volume_entity` | entity ID | `sensor.pvl_reservoir_slapy_volume` | Current reservoir volume sensor. |
| `precipitation_24h_entity` | entity ID | `sensor.pvl_reservoir_slapy_precipitation_24h` | Rolling 24-hour precipitation sensor. |
| `air_temperature_entity` | entity ID | `sensor.pvl_reservoir_slapy_air_temperature` | Current air temperature sensor. |
| `min_level` | number (m) | `220` | Lower limit of the level gauge. |
| `max_level` | number (m) | `273` | Upper limit of the level gauge; must be greater than `min_level`. |
| `show_history` | boolean | `true` | Show the one-hour and 24-hour Recorder history chart. |
| `references` | list of `{name, level}` | Three Slapy examples | Named reference levels for the selectable level difference. Set `[]` to hide the reference selector. |
| `reference_key` | string | Water-level entity ID | Optional browser storage key for the selected reference. |

For backward compatibility, the previous `entities:` mapping (`water_level`, `inflow`, `outflow`, `volume`, `precipitation_24h`, `air_temperature`) is also accepted. Explicit `*_entity` options take precedence. The selected reference remains stored in browser local storage and is not synchronized across devices. History is read from Home Assistant Recorder; the card does not contact PVL.

## Sensors

| Sensor | Home Assistant unit | Notes |
| --- | --- | --- |
| Water level | m | Elevation in PVL's Balt p. v. vertical system |
| Volume | m³ | Converted from PVL's million m³ value |
| Inflow | m³/s | Current inflow |
| Outflow | m³/s | Current outflow |
| Precipitation 24h | mm | Rolling 24-hour value; no forced updates |
| Air temperature | °C | Current value |

Home Assistant Recorder stores state changes according to its configuration. Keep the water-level entity included in Recorder for the card charts. Recorder retention controls how much raw history is available.

## Development

Run parser tests with the Python standard library:

```sh
python3 -m unittest discover -s tests -v
```

The project workspace does not include the Home Assistant Python package. A complete integration setup test must be run in a Home Assistant development environment.

## HACS publication checklist

- Create a public GitHub repository and set its description and topics.
- Replace `OWNER` in `custom_components/pvl_reservoir/manifest.json` with the GitHub account or organization and repository name.
- Decide whether to distribute the card in a separate HACS dashboard repository or document manual installation.
- Run Home Assistant and HACS validation in the target development environment before publishing.
